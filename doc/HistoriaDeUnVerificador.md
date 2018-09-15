Historia de un Verificador
===============

1. Llego a la fábrica, al puesto donde voy a trabajar (Centre) y digo que ya estoy aquí(centre.operator).
2. Consulto qué pieza tengo que procesar y qué hacer con ella (Operation(partnumber, name))
3. Empiezo a trabajar(Shift)
4. Trabajo pieza a pieza o por lote (Batch) con una cantidad fija (batch.qty)
5. Tengo una lista de verificación (test) creada  a partir de un plan de control  y asociada a un batch, la recorro punto por punto (test.checks). Tengo dos opciones, acabar hasta el final de la verificación  o parar al primer _fallo_. Eso me lo tienen que marcar.
6. En cada chequeo debo decidir si es OK o NOK(check.result). Si es NOK será porque hay uno o varios fallos (check.failures). Además hay características (check.chars)  que exigen una medición  que da valor numérico (check.chars.value)
7. Dependiendo de la directriz inicial, acabo hasta el final o paro al primer fallo.
8. Vuelvo a 4 hasta que acabe el turno(shift)



