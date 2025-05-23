import smtplib
import imaplib
import poplib
import email
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_email_smtp(recipient, subject, message, task=None):
    sender = settings.EMAIL_HOST_USER

    if task:
        html_content = render_to_string(
            'emails/task_email.html',
            {'task': task, 'user_message': message}
        )
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject,
            text_content,
            sender,
            [recipient]
        )
        email.attach_alternative(html_content, "text/html")
        return email.send()
    else:
        return send_mail(
            subject,
            message,
            sender,
            [recipient],
            fail_silently=False,
        )


def check_email_imap(last_n=5):
    mail = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
    try:
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select('inbox')

        status, data = mail.search(None, 'ALL')
        if status != 'OK':
            raise Exception(f"Failed to search messages: {status}")

        mail_ids = data[0].split()

        if not mail_ids:
            mail.close()
            mail.logout()
            return []

        emails = []
        start_index = max(0, len(mail_ids) - last_n)

        for i in range(start_index, len(mail_ids)):
            status, data = mail.fetch(mail_ids[i], '(RFC822)')
            if status != 'OK':
                continue

            for response_part in data:
                if isinstance(response_part, tuple):
                    message = email.message_from_bytes(response_part[1])

                    mail_from = message['from']
                    mail_subject = message['subject']

                    if mail_subject:
                        decoded_header = decode_header(mail_subject)
                        mail_subject = ''
                        for part, encoding in decoded_header:
                            if isinstance(part, bytes):
                                mail_subject += part.decode(encoding or 'utf-8', errors='replace')
                            else:
                                mail_subject += part

                    mail_content = ""
                    if message.is_multipart():
                        for part in message.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if "attachment" in content_disposition:
                                continue

                            if content_type == "text/plain":
                                try:
                                    payload = part.get_payload(decode=True)
                                    charset = part.get_content_charset() or 'utf-8'
                                    mail_content = payload.decode(charset, 'replace')
                                    break
                                except Exception as e:
                                    mail_content += f"[Error decoding message: {str(e)}]"
                    else:
                        try:
                            payload = message.get_payload(decode=True)
                            charset = message.get_content_charset() or 'utf-8'
                            mail_content = payload.decode(charset, 'replace')
                        except Exception as e:
                            mail_content = f"[Error decoding message: {str(e)}]"

                    emails.append({
                        'from': mail_from,
                        'subject': mail_subject,
                        'content': mail_content[:100] + '...' if len(mail_content) > 100 else mail_content,
                        'date': message['date']
                    })

        mail.close()
        mail.logout()
        return emails

    except Exception as e:
        print(f"Error in IMAP: {e}")
        return []


def check_email_pop3(last_n=5):
    server = poplib.POP3_SSL(settings.POP3_SERVER, settings.POP3_PORT)
    try:
        server.user(settings.EMAIL_HOST_USER)
        server.pass_(settings.EMAIL_HOST_PASSWORD)

        status, msg_list, octets = server.list()
        if not msg_list:
            server.quit()
            return []

        num_messages = len(msg_list)

        emails = []
        for i in range(max(1, num_messages - last_n + 1), num_messages + 1):
            try:
                status, msg_lines, octets = server.retr(i)
                raw_email = b"\n".join(msg_lines)
                parsed_email = email.message_from_bytes(raw_email)

                mail_from = parsed_email['From']
                mail_subject = parsed_email['Subject']

                if mail_subject:
                    decoded_header = decode_header(mail_subject)
                    mail_subject = ''
                    for part, encoding in decoded_header:
                        if isinstance(part, bytes):
                            mail_subject += part.decode(encoding or 'utf-8', errors='replace')
                        else:
                            mail_subject += part

                mail_content = ""
                if parsed_email.is_multipart():
                    for part in parsed_email.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if "attachment" in content_disposition:
                            continue

                        if content_type == "text/plain":
                            try:
                                payload = part.get_payload(decode=True)
                                charset = part.get_content_charset() or 'utf-8'
                                mail_content = payload.decode(charset, 'replace')
                                break
                            except Exception as e:
                                mail_content += f"[Error decoding message: {str(e)}]"
                else:
                    try:
                        payload = parsed_email.get_payload(decode=True)
                        charset = parsed_email.get_content_charset() or 'utf-8'
                        mail_content = payload.decode(charset, 'replace')
                    except Exception as e:
                        mail_content = f"[Error decoding message: {str(e)}]"

                emails.append({
                    'from': mail_from,
                    'subject': mail_subject,
                    'content': mail_content[:100] + '...' if len(mail_content) > 100 else mail_content,
                    'date': parsed_email['Date']
                })
            except Exception as e:
                print(f"Error processing message {i}: {e}")
                continue

        server.quit()
        return emails

    except Exception as e:
        print(f"Error in POP3: {e}")
        return []

def test_mail_protocols():
    results = {
        'smtp': None,
        'imap': None,
        'pop3': None
    }

    try:
        send_email_smtp(
            settings.EMAIL_HOST_USER,
            "SMTP Test",
            "This is a test message sent using SMTP."
        )
        results['smtp'] = "Success"
    except Exception as e:
        results['smtp'] = f"Error: {str(e)}"

    try:
        emails = check_email_imap(1)
        results['imap'] = f"Success: Found {len(emails)} emails"
    except Exception as e:
        results['imap'] = f"Error: {str(e)}"

    try:
        emails = check_email_pop3(1)
        results['pop3'] = f"Success: Found {len(emails)} emails"
    except Exception as e:
        results['pop3'] = f"Error: {str(e)}"

    return results