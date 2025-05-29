import pymongo
import pandas as pd
import argparse
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email import encoders
import sys


def send_excel_email(filename, recipient_email, sender_email, smtp_password, smtp_server='smtp.gmail.com', smtp_port=587):
    # Check file size (15MB = 15 * 1024 * 1024 bytes)
    if os.path.getsize(filename) > 15 * 1024 * 1024:
        raise ValueError(
            "Excel file is larger than 15MB. Cannot send via email.")

    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "User Selections Data Export"

    body = "Please find attached the user selections data export."
    msg.attach(MIMEText(body, 'plain'))

    # Attach file
    with open(filename, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename= {os.path.basename(filename)}'
    )
    msg.attach(part)

    # Send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, smtp_password)
        server.send_message(msg)


def main():
    parser = argparse.ArgumentParser(
        description='Export MongoDB data to Excel and optionally email it')
    parser.add_argument('--email', type=str,
                        help='Email address to send the Excel file to')
    parser.add_argument('--smtp-user', type=str,
                        help='SMTP username (email address to send from)')
    parser.add_argument('--smtp-password', type=str,
                        help='SMTP password or app password')
    parser.add_argument('--smtp-server', type=str, default='smtp.gmail.com',
                        help='SMTP server (default: smtp.gmail.com)')
    parser.add_argument('--smtp-port', type=int, default=587,
                        help='SMTP port (default: 587)')
    args = parser.parse_args()

    # Connect to MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["billa_telegram_bot"]
    collection = db["metadata"]

    # MongoDB aggregation pipeline
    pipeline = [
        {
            "$group": {
                "_id": {
                    "user": "$user_name",
                    "selection": "$selection_path"
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$group": {
                "_id": "$_id.user",
                "selections": {
                    "$push": {
                        "selection_path": "$_id.selection",
                        "count": "$count"
                    }
                },
                "total_selections": {"$sum": "$count"}
            }
        },
        {"$sort": {"total_selections": -1}}
    ]

    # Execute aggregation and fetch results
    results = list(collection.aggregate(pipeline))

    # Prepare data for DataFrame
    flattened_data = []
    for user_data in results:
        user = user_data['_id']
        for selection in user_data['selections']:
            flattened_data.append({
                'User': user,
                'Selection Path': selection['selection_path'],
                'Count': selection['count']
            })

    # Convert to DataFrame
    df = pd.DataFrame(flattened_data)

    # Save to Excel
    output_file = "user_selections.xlsx"
    df.to_excel(output_file, index=False)

    print(f"Data exported to {output_file}")

    if args.email:
        if not args.smtp_user or not args.smtp_password:
            print(
                "Error: --smtp-user and --smtp-password are required when using --email", file=sys.stderr)
            sys.exit(1)
        try:
            send_excel_email(output_file, args.email, args.smtp_user, args.smtp_password,
                             args.smtp_server, args.smtp_port)
            print(f"Excel file sent to {args.email}")
        except Exception as e:
            print(f"Error sending email: {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
