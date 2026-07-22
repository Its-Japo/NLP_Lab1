# NLP_Lab1
Lab 1 de procesamiento de lenguaje natural


---

# Reflexión de laboratorio: 

Falsos positivos: el patron PHONE se afino al formato de Guatemala (8 digitos
4-4, con +502 opcional), lo que evita confundir un DPI con un telefono; aun asi,
cualquier numero de 8 digitos con esa forma —un codigo de factura o de cuenta—
se marcara como telefono. LONG_NUMBER agrava esto porque cualquier numero de 8 o
mas digitos se considera sensible aunque sea un codigo de producto inofensivo.
EMAIL tambien puede disparar sobre cadenas tipo "usuario@host" que no son correos
reales.

Falsos negativos: la regex no detecta correos ofuscados ("ana [arroba] uvg punto
gt"), telefonos escritos con palabras, URLs sin http ni www, secretos con
nombres distintos a los del diccionario, o un DPI partido en varias lineas. Todo
dato sensible expresado de forma no estandar escapa a los patrones.

Perdida de informacion al redactar: al reemplazar por [EMAIL_REDACTED] o
[PHONE_REDACTED] se pierde el dato concreto, pero tambien el contexto: el modelo
ya no sabe cuantos correos habia, a quien pertenecen ni si dos menciones son la
misma persona. Esto puede degradar tareas que dependian de esa entidad.

Suficiencia de Regex: no. Regex es una primera capa util y barata, pero fragil
ante variantes y ofuscacion; en una empresa real generaria fugas y falsos
positivos costosos. Como capas adicionales agregaria NER/ML para deteccion
semantica de PII, diccionarios y listas de bloqueo mantenidas, deteccion de
secretos por entropia, cifrado y control de acceso, y registro de auditoria con
revision humana antes de enviar datos a un modelo externo.