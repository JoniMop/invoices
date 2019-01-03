import sys
import os
import imaplib
import getpass
import email
import email.header
import datetime
import json
#Cuenta de correo gmail
EMAIL_ACCOUNT = "test@gmail.com"

# Buzon de la cuenta en donde se hace la busqueda de correos/emails
EMAIL_FOLDER = "INBOX"


def process_mailbox(M):
    """

    """

    rv, data = M.search(None, "UNSEEN")
    if rv != 'OK':
        print("No messages found!")
        return

    for num in data[0].split():
        rv, data = M.fetch(num, '(RFC822)')
        if rv != 'OK':
            print("ERROR getting message", num)
            return
#Partes del mensaje
        msg = email.message_from_bytes(data[0][1])
        hdr = email.header.make_header(email.header.decode_header(msg['Subject']))
        subject = str(hdr)

#Formtear fecha del mensaje para generar id del correo (dateid)
        date_tuple = email.utils.parsedate_tz(msg['Date'])
        local_date = datetime.datetime.fromtimestamp(
            email.utils.mktime_tz(date_tuple))
        dateid = local_date.strftime('%Y%m%d%H%M%S%f')

#Procesamiento de adjuntos
        if msg.get_content_maintype() != 'multipart':
            return
        # crea directorio por cada correo
        if not os.path.exists(dateid):
            os.makedirs(dateid)
        #Recorre cada adjunto en el correo(msg)
        for part in msg.walk():
            if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                open('.' + '/' + dateid + '/' + part.get_filename(), 'wb').write(part.get_payload(decode=True))
#

#JSON
        jsondata = {}

        jsondata[dateid] = subject

        with open('data.json', 'w') as outfile:
            json.dump(jsondata, outfile)

        print('Message %s: %s' % (num, subject))
        print('Raw Date:', msg['Date'])
        # Now convert to local date-time
        date_tuple = email.utils.parsedate_tz(msg['Date'])
        if date_tuple:
            local_date = datetime.datetime.fromtimestamp(
                email.utils.mktime_tz(date_tuple))
            print ("Local Date:", \
                local_date.strftime("%a, %d %b %Y %H:%M:%S"))




#PRINCIPAL

#Servidor imap de googlemail
M = imaplib.IMAP4_SSL('imap.gmail.com')

#Intenta login
try:
    rv, data = M.login(EMAIL_ACCOUNT, getpass.getpass())
except imaplib.IMAP4.error:
    print ("LOGIN FAILED!!! ")
    sys.exit(1)

#Imprime resultado de login
print(rv, data)

#Imprime los buzones de correo de la cuenta
rv, mailboxes = M.list()
if rv == 'OK':
    print("Mailboxes:")
    print(mailboxes)

#Procesa los datos del buzon definido en EMAIL_FOLDER(INBOX)
rv, data = M.select(EMAIL_FOLDER)
if rv == 'OK':
    print("Processing mailbox...\n")
    process_mailbox(M)
    M.close()
else:
    print("ERROR: Unable to open mailbox ", rv)

#Cierra sesion
M.logout()
