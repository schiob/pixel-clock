package main

import (
	"machine"
	"time"

	"tinygo.org/x/drivers/font"
	"tinygo.org/x/drivers/hub75"
)

func main() {
	// Configuración de los pines de acuerdo a la documentación de TinyGo para MatrixPortal M4
	p := hub75.Pins{
		R1:  machine.PA01,
		G1:  machine.PA02,
		B1:  machine.PA05,
		R2:  machine.PA06,
		G2:  machine.PA07,
		B2:  machine.PA04,
		A:   machine.PA23,
		B:   machine.PB22,
		C:   machine.PB23,
		D:   machine.PA27,
		E:   machine.PA20,
		CLK: machine.PA16,
		LAT: machine.PA19,
		OE:  machine.PA21,
	}

	// Inicializar la interfaz Hub-75 con los pines configurados
	display := hub75.New(p)

	if err := display.Configure(); err != nil {
		// Si ocurre un error en la configuración, encender/apagar un LED de la placa para indicar el problema
		machine.LED.Configure(machine.PinConfig{Mode: machine.PinOutput})
		for {
			machine.LED.High()
			time.Sleep(time.Second)
			machine.LED.Low()
			time.Sleep(time.Second)
		}
	}

	// Activar la salida (OE = false significa salida activada)
	display.SetOE(false)

	// Texto a mostrar
	text := "HOLA"
	// Renderizar el texto utilizando una fuente predefinida, por ejemplo Font6x8
	pixelBuffer := font.RenderText(text, font.Font6x8)

	for {
		display.Clear()
		// Dibujar el texto en el display
		display.DrawPixelBuffer(pixelBuffer)
		// Actualizar el display
		display.Update()

		// Desplazar el texto para crear animación (opcional)
		pixelBuffer = font.ScrollLeft(pixelBuffer)

		time.Sleep(100 * time.Millisecond)
	}
}
