# Clasificador de imágenes

Agente que clasifica imágenes de alimentos entre 40 categorías mediante una red neuronal profunda.

## Instalación de dependencias

Se requiere tener instalada la última versión de TensorFlow (2.X). Puede ser fácilmente instalada con `pip` o con `conda`:

* `pip install --upgrade tensorflow`

* `conda install tensorflow`

**Nota:** Aunque no es necesario, la versión de TensorFlow con soporte para GPU mejora el rendimiento del sistema.

## Ejecución del agente

Tan sólo se debe crear el agente SPADE del tipo `ImageAgent`. Este agente espera recibir mensajes con performativa Request (`{"performative": "request"}`), en cuyo cuerpo se indique la ruta de la imagen a clasificar. Un ejemplo de mensaje sería el siguiente:

```python
msg = Message(to="agent_jid@domain")
# Set the "request" FIPA performative
msg.set_metadata("performative", "request")
# Set the message content
msg.body = 'test_imgs/IMG_0001.jpg')
```
