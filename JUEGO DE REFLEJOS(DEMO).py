from machine import Pin, mem32    
import time, random            

#  SALIDAS (LEDs y BUZZER)
LED1, LED2, LED3, BUZ = 2, 4, 5, 18   #  pines donde conectamos los 3 LEDs y el buzzer.

for p in (LED1, LED2, LED3, BUZ):    #Recorremos cada pin
    Pin(p, Pin.OUT)                  # configuramos como salida digital.

# Encendido/apagado rápido usando registros del ESP32
SET, CLR = 0x3FF44008, 0x3FF4400C    # Direcciones especiales de memoria (SET=encender, CLR=apagar).
def on(mask):  mem32[SET] = mask     # Enciende los pines que diga la máscara binaria.
def off(mask): mem32[CLR] = mask     #Apaga " "
def all_off():                       ### Apaga todos los LEDs y buzzer de una vez.
    off((1<<LED1)|(1<<LED2)|(1<<LED3)|(1<<BUZ))

# ENTRADAS (BOTONES) 
# Botones del jugador 1
J1 = [ Pin(13, Pin.IN, Pin.PULL_DOWN),
       Pin(14, Pin.IN, Pin.PULL_DOWN),  
       Pin(27, Pin.IN, Pin.PULL_DOWN), 
       Pin(26, Pin.IN, Pin.PULL_DOWN) ] 

# Botones del jugador 2
J2 = [ Pin(25, Pin.IN, Pin.PULL_DOWN), 
       Pin(23, Pin.IN, Pin.PULL_DOWN),
       Pin(22, Pin.IN, Pin.PULL_DOWN),  
       Pin(21, Pin.IN, Pin.PULL_DOWN) ]

# Botones de control del juego
START   = Pin(19, Pin.IN, Pin.PULL_DOWN)   
FINISH  = Pin(16, Pin.IN, Pin.PULL_DOWN)   
MODO_INV = Pin(17, Pin.IN, Pin.PULL_DOWN)  

# ESTÍMULOS 
STIM = [
    (1<<LED1, [J1[0], J2[0]]),   ### Estímulo : LED → botón correcto J1[0] o J2[0].
    (1<<LED2, [J1[1], J2[1]]),   
    (1<<LED3, [J1[2], J2[2]]),   
    (1<<BUZ , [J1[3], J2[3]])    
]

#ANTIRREBOTE
def leer_boton(pin):              # Función para leer un botón
    if pin.value():               # Si el botón está presionado...
        time.sleep_ms(50)         #esperamos 50 ms para filtrar rebotes.
        if pin.value():           # Si después de 50 ms aún está presionado:
            while pin.value():    # Esperamos a que lo suelte.
                pass
            return True           # Confirmamos que fue una pulsación válida.
    return False                  # Si no, devolvemos False.

#JUEGO CLÁSICO
def clasico(players=2):                  #Función para jugar en modo clásico.
    puntos = {"J1": 0, "J2": 0}          # marcador inicial (0 para cada jugador).
    print(" Modo CLÁSICO. Pulsa START para comenzar...")

    while not START.value():             ### Espera hasta que alguien pulse START.
        time.sleep_ms(50)

    ronda = 0
    activos = J1 if players == 1 else (J1 + J2)   #Si es 1 jugador → solo botones J1. Si son 2 → J1+J2.

    while not FINISH.value():            # Se repite hasta que se pulse FINISH.
        ronda += 1                       # Aumentamos el número de ronda.
        all_off()                        # Apagamos todo antes de cada ronda.
        time.sleep(random.uniform(1, 5)) # Pausa aleatoria de 1 a 5 segundos.

        stim, correctos = random.choice(STIM)  # Escogemos estímulo aleatorio 
        on(stim)                          # Encendemos ese estímulo.
        t0 = time.ticks_ms()              # Guardamos tiempo de inicio.
        ganador, t_win = None, None       # Inicializamos sin ganador ni tiempo.

        # Ventana de respuesta de 3 segundos
        while time.ticks_diff(time.ticks_ms(), t0) < 3000 and not FINISH.value():
            if leer_boton(MODO_INV):      ### Si se presiona el botón de modo (GPIO17):
                print(" Cambio de modo detectado")
                return "MODO"             ### Terminamos aquí para cambiar a modo inverso.

            for i, pin in enumerate(activos):   ### Recorremos los botones activos.
                if leer_boton(pin):             ### Si alguien presionó un botón:
                    jugador = "J1" if (players==1 or i < 4) else "J2"  ### Si el índice <4 → jugador 1, si no → jugador 2.
                    correcto = correctos[0] if jugador=="J1" else correctos[1]  ### Botón correcto según jugador.

                    if pin is correcto:         ### Si fue el botón correcto:
                        dt = time.ticks_diff(time.ticks_ms(), t0)  ### Calculamos tiempo de reacción.
                        if (ganador is None) or (dt < t_win):      ### Si no había ganador o fue más rápido:
                            ganador, t_win = jugador, dt            ### Guardamos ganador y su tiempo.
                    else:                       ### Si fue botón incorrecto:
                        puntos[jugador] -= 1    ### Restamos 1 punto de penalización.
                        print(f"{jugador}  se equivocó (-1)")

        off(stim)                             ### Apagamos el estímulo después de la ventana de respuesta.

        if ganador:                           ### Si hubo ganador...
            puntos[ganador] += 1              ### ...sumamos 1 punto a ese jugador.
            print(f" Ronda {ronda}: {ganador} gana en {t_win} ms (+1)")
        else:
            print(f" Ronda {ronda}: Nadie acertó")  ### Si nadie presionó.

        print("Marcador:", puntos)            ### Mostramos puntaje actualizado.
    return puntos

# -------------------- JUEGO INVERSO --------------------
def inverso(rondas=5):                       ### Función para jugar en modo inverso (solo jugador 1).
    puntos = 0
    leds = [LED1, LED2, LED3]                ### Lista de LEDs usados.
    btns = [J1[0], J1[1], J1[2]]             ### Botones correspondientes del jugador 1.
    print(" Modo INVERSO (elige el LED que NO se prendió)")

    for r in range(rondas):                  ### Bucle de rondas (por defecto 5).
        idx = [0,1,2]                        ### Identificamos LEDs por índices: 0=LED1, 1=LED2, 2=LED3.
        wrong = random.choice(idx)           ### Escogemos al azar uno que quedará APAGADO (respuesta correcta).
        show = [i for i in idx if i != wrong]### Los otros dos LEDs → los que sí se prenden.

        on((1<<leds[show[0]])|(1<<leds[show[1]]))  ### Encendemos los dos LEDs de "show".
        t0 = time.ticks_ms(); ok = False     ### Guardamos tiempo inicial y bandera ok.

        while time.ticks_diff(time.ticks_ms(), t0) < 2000 and not FINISH.value():
            if leer_boton(MODO_INV):         ### Si se presiona botón de modo:
                print(" Cambio de modo detectado")
                return "MODO"

            if leer_boton(btns[wrong]):      ### Si presiona el LED apagado → gana punto.
                puntos+=1; ok=True; break
            for j in show:                   ### Si presiona uno de los LEDs encendidos → pierde punto.
                if leer_boton(btns[j]):
                    puntos-=1; ok=True; break
            if ok: break                     ### Salimos si ya hubo respuesta.

        off((1<<leds[show[0]])|(1<<leds[show[1]]))  ### Apagamos los LEDs que estaban encendidos.
        print("Ronda", r+1, "Puntos:", puntos)      ### Mostramos resultados de la ronda.
    return {"J1": puntos}                   ### Devolvemos el puntaje del jugador 1.

# -------------------- PROGRAMA PRINCIPAL --------------------
if __name__ == "__main__":                  ### Punto de inicio del programa.
    all_off()                               ### Aseguramos que todo empiece apagado.
    jugadores = int(input("¿Cuántos jugadores? (1/2): ") or "2")  ### Preguntamos cantidad de jugadores.
    modo_inverso = False                    ### Arrancamos en modo clásico por defecto.

    print(" START = iniciar | FINISH = terminar | GPIO17 = cambiar modo")

    while not FINISH.value():               ### Bucle principal hasta que se pulse FINISH.
        if modo_inverso:                    ### Si está en modo inverso...
            resultado = inverso(3)          ### ...jugamos 3 rondas inversas.
        else:
            resultado = clasico(jugadores)  ### Si no, jugamos modo clásico.

        if resultado == "MODO":             ### Si detectamos cambio de modo...
            modo_inverso = not modo_inverso ### ...invertimos el estado.
            print(" CAMBIADO A", "INVERSO" if modo_inverso else "CLÁSICO")
            continue                        ### Volvemos al bucle con el nuevo modo.

        print("Resultados parciales:", resultado)   ### Mostramos resultados parciales.

    print(" Juego terminado. Resultados finales:", resultado)  ### Mostramos resultados finales.
