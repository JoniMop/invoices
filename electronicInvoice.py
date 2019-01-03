#!/usr/bin/python3
#
#
import sys
import os
import imaplib
import getpass
import email
import email.header
import datetime
import json
import glob
from xml.etree import ElementTree


#
def busca_facturas(M):
    """

    :param M: Conexion IMAP4SSL
    :return:
    """

    # Recorrer la rutina por cada keyword
    for i in range(5):

        # Busca los correos no leidos
        if i == 0:
            rv, data = M.search(None, '(UNSEEN)', 'SUBJECT', 'Pago')

        if i == 1:
            rv, data = M.search(None, '(UNSEEN)', 'SUBJECT', 'XML')

        if i == 2:
            rv, data = M.search(None, '(UNSEEN)', 'SUBJECT', 'Facturas')

        if i == 3:
            rv, data = M.search(None, '(UNSEEN)', 'SUBJECT', 'Documento')

        if i == 4:
            rv, data = M.search(None, '(UNSEEN)', 'SUBJECT', 'Factura')

        if rv != 'OK':
            print("No se encontraron mensajes!")
            return

        # Recorrer cada correo
        for num in data[0].split():
            #ver: https://pymotw.com/3/imaplib/#whole-messages
            rv, data = M.fetch(num, '(RFC822)')
            if rv != 'OK':
                print("ERROR no se pudo obtener el mensaje", num)
                return

            # Guardar partes del correo en variables
            msg = email.message_from_bytes(data[0][1])
            hdr = email.header.make_header(email.header.decode_header(msg['Subject']))
            subject = str(hdr)

            # Formtear fecha del mensaje para print
            date_tuple = email.utils.parsedate_tz(msg['Date'])
            local_date = datetime.datetime.fromtimestamp(
                email.utils.mktime_tz(date_tuple))

            #Generar dateid (valor unico)con la fecha del correo
            dateid = local_date.strftime('%Y%m%d%H%M%S%f')

            # Procesar adjuntos
            if msg.get_content_maintype() != 'multipart':
                return
            # Crea directorio por cada correo con el valor dateid
            if not os.path.exists(dateid):
                os.makedirs(dateid)

            # Recorre cada adjunto en el correo(msg) y lo agrega en la carpeta
            for part in msg.walk():
                if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                    open('.' + '/' + dateid + '/' + part.get_filename(), 'wb').write(part.get_payload(decode=True))

            #Obtener datos del archivo XML
            facturas_xml = glob.glob('.' + '/' + dateid + '/*.xml')  #
            facturas_xmltree = ElementTree.parse(facturas_xml[0])

            #Guardar raiz de XML en variable
            root = facturas_xmltree.getroot()

            #Llama a funcion recursiva que carga DATOS_XML
            recur_node(root)

            # Si existen datos
            if data[0] == b'':  # No hay correos
                print("No hay correos con este keyword")
                return
            else:
                print("Actualizando facturas.json")

                with open("facturas.json", "a") as data:
                    information = {}
                    #Keys y valores para json

                    #Agregar datos de correo en json
                    information[dateid] = subject

                    #Agregar datos de xml en json
                    for d in DATOS_XML:
                        key  = ''
                        #Llamar funcion para acortar la clave
                        key = limpia_datosxml(d)

                        information[key] = DATOS_XML[d]

                    data.write(json.dumps(information, indent=4))
                    data.close()

            # Imprimir datos del correo en consola
                print('Mensaje %s: %s' % (num, subject))
                print('Fecha:', msg['Date'])
            # Convertir a fecha local
                date_tuple = email.utils.parsedate_tz(msg['Date'])
                if date_tuple:
                    local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                    print("Fecha Local:", \
                      local_date.strftime("%a, %d %b %Y %H:%M:%S"))


def recur_node(node):
    """
    Funcion recursiva para recorrer todos los elements del xml
    :param node: el nodo xml inicial (raiz)
    :return: 0 cuando termina
    """
    if node != None:

        for item in node.getchildren():
            DATOS_XML[item.tag] = item.text
            recur_node(item)
    else:
        return 0

def limpia_datosxml(str):
    """
    Funcion para eliminar el URL de factura electronica de las claves
    :param str: El texto del xml que se va a limpiar
    :return: str: la cadena de texto sin el URL
    """
    if str.startswith('{https://tribunet.hacienda.go.cr/docs/esquemas/2017/v4.2/facturaElectronica}'):
        str = str[76:]

    return str



# PRINCIPAL

#VARIABLES DEL SCRIPT
#Diccionario de datos XML usado dentro de funciones
DATOS_XML = {}

# Cuenta de correo gmail
EMAIL_ACCOUNT = "test@gmail.com"

# Buzon de la cuenta en donde se hace la busqueda de correos
EMAIL_FOLDER = "INBOX"

# Servidor imap de googlemail
M = imaplib.IMAP4_SSL('imap.gmail.com')


def main():
    """
    Main del script getFacturaElectronica.py
    :return:
    """
    # Intentar login
    try:
        rv, data = M.login(EMAIL_ACCOUNT, getpass.getpass())
    except imaplib.IMAP4.error:
        print("Login fallido!!! ")
        sys.exit(1)

    # Imprimir resultado de login
    print(rv, data)

    # Imprimir la lista de buzones de correo en la cuenta (esto es informacion adicional)
    rv, mailboxes = M.list()
    if rv == 'OK':
        print("Cuentas de correo:")
        print(mailboxes)

    # Procesar los datos del buzon definido en EMAIL_FOLDER(INBOX)
    rv, data = M.select(EMAIL_FOLDER)
    if rv == 'OK':
        print("Procesando cuenta de correo...\n")
        busca_facturas(M)
        M.close()
    else:
        print("ERROR: no se pudo abrir la cuenta de correo ", rv)

    # Cierra sesion
    M.logout()

if __name__ == "__main__":
    sys.exit(main())
