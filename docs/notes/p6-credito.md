# p6 Crédito y tipos

Añadidos (todo existente se mantiene):
- Crédito y endeudamiento: `newhh` (nuevo crédito vivienda y consumo, toggle suma 12 meses / variación anual) y `newcorp` (sociedades no financieras, mismo toggle). Separados por escala (sociedades ~5x vivienda).
- Deuda pública: `deficit` (barras España y UE-27, ref 0) e `interest` (líneas ES, UE-27, DE, FR, IT).
Pruebas: 375 y 1440 px, 0 errores de consola, 0 peticiones fallidas, sin desbordamiento ni error-card; toggles probados.
