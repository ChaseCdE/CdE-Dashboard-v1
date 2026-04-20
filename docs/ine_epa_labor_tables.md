# INE EPA Labor Market Tables Reference

This document contains the specific table IDs and series codes for labor market indicators from the EPA (Encuesta de Poblacion Activa) survey provided by INE (Instituto Nacional de Estadistica).

**API Base Endpoint:** `https://servicios.ine.es/wstempus/js/ES/`

**EPA Operation Code:** 293

---

## 1. Tasa de Empleo (Employment Rate)

The percentage of working-age population that is employed.

### Primary Tables

| Table ID | Table Name (Spanish) | Frequency | Coverage |
|----------|---------------------|-----------|----------|
| **14508** | Tasas de empleo por distintos grupos de edad, sexo y comunidad autonoma | Quarterly | Historical |
| **65305** | Tasas de empleo por distintos grupos de edad, sexo y comunidad autonoma | Quarterly | Current (2021 base) |
| **65349** | Tasas de actividad, paro y empleo por provincia y sexo | Quarterly | Provincial level |

### Key Series Codes (Table 14508/65305)

| Series Code | Description |
|-------------|-------------|
| **EPA441060** | Tasa de empleo. Total Nacional. Ambos sexos. 16 y mas anos |
| **EPA441062** | Tasa de empleo. Total Nacional. Ambos sexos. Menos de 25 anos |
| **EPA441066** | Tasa de empleo. Total Nacional. Ambos sexos. 25-54 anos |
| **EPA441067** | Tasa de empleo. Total Nacional. Ambos sexos. 55 y mas anos |
| **EPA441027** | Tasa de empleo. Total Nacional. Hombres. 16 y mas anos |
| **EPA440924** | Tasa de empleo. Total Nacional. Mujeres. 16 y mas anos |

### Combined Rates Table (65349)

| Series Code | Description |
|-------------|-------------|
| **EPA442577** | Tasa de empleo. Total Nacional. Ambos sexos |
| **EPA442677** | Tasa de empleo. Total Nacional. Hombres |
| **EPA442777** | Tasa de empleo. Total Nacional. Mujeres |

### Additional Tables (EU Indicators 20-64 years)

| Table ID | Table Name | Notes |
|----------|------------|-------|
| **67548** | Tasa de empleo de las personas entre 20 y 64 anos por sexo y grupo de edad | EU2020 indicator |
| **67555** | Tasa de empleo de las personas entre 20 y 64 anos por sexo y Comunidad Autonoma | Regional breakdown |

---

## 2. Tasa de Actividad (Labor Force Participation Rate)

The percentage of working-age population that is economically active (employed or seeking employment).

### Primary Tables

| Table ID | Table Name (Spanish) | Frequency | Coverage |
|----------|---------------------|-----------|----------|
| **14509** | Tasas de actividad por distintos grupos de edad, sexo y comunidad autonoma | Quarterly | Historical |
| **65295** | Tasas de actividad por distintos grupos de edad, sexo y comunidad autonoma | Quarterly | Current (2021 base) |
| **65081** | Tasas de actividad por sexo y grupo de edad | Quarterly | National by age |
| **72978** | Tasas de actividad por sexo y grupo de edad | Quarterly | Latest methodology |

### Key Series Codes

| Series Code | Description |
|-------------|-------------|
| **EPA388079** | Tasa de actividad. Total Nacional. Ambos sexos. 16 y mas anos |
| **EPA388093** | Tasa de actividad. Total Nacional. Hombres. 16 y mas anos |
| **EPA388106** | Tasa de actividad. Total Nacional. Mujeres. 16 y mas anos |
| **EPA436340** | Tasa de actividad. Total Nacional. Ambos sexos. Menos de 25 anos |
| **EPA436342** | Tasa de actividad. Total Nacional. Ambos sexos. 25-54 anos |
| **EPA436343** | Tasa de actividad. Total Nacional. Ambos sexos. 55 y mas anos |

### Combined Rates Table (65349)

| Series Code | Description |
|-------------|-------------|
| **EPA438090** | Tasa de actividad. Total Nacional. Ambos sexos |
| **EPA438210** | Tasa de actividad. Total Nacional. Hombres |
| **EPA438330** | Tasa de actividad. Total Nacional. Mujeres |

---

## 3. Ocupados (Total Employed Persons)

Absolute number of employed persons.

### Primary Tables

| Table ID | Table Name (Spanish) | Frequency | Coverage |
|----------|---------------------|-----------|----------|
| **65109** | Ocupados por sexo y grupo de edad | Quarterly | National by age/sex |
| **65302** | Ocupados por grupo de edad, sexo y comunidad autonoma | Quarterly | Regional breakdown |
| **72982** | Ocupados por sexo y grupo de edad | Quarterly | Latest methodology |

### Key Series Codes (Table 65109)

| Series Code | Description | Unit |
|-------------|-------------|------|
| **EPA387796** | Ocupados. Total Nacional. Ambos sexos. 16 y mas anos | Miles de personas |
| **EPA387880** | Ocupados. Total Nacional. Hombres. 16 y mas anos | Miles de personas |
| **EPA387960** | Ocupados. Total Nacional. Mujeres. 16 y mas anos | Miles de personas |
| **EPA387808** | Ocupados. Total Nacional. Ambos sexos. 16-19 anos | Miles de personas |
| **EPA387814** | Ocupados. Total Nacional. Ambos sexos. 20-24 anos | Miles de personas |
| **EPA387820** | Ocupados. Total Nacional. Ambos sexos. 25-29 anos | Miles de personas |

---

## 4. Tasa de Temporalidad (Temporary Contract Rate)

Percentage of employees with temporary contracts.

### Primary Tables

| Table ID | Table Name (Spanish) | Frequency | Coverage |
|----------|---------------------|-----------|----------|
| **65194** | Asalariados por sexo y tipo de contrato o relacion laboral | Quarterly | Current |
| **10898** | Porcentaje de asalariados con contrato temporal segun periodo | Annual | Summary indicator |
| **4241** | Asalariados por tipo de contrato, sexo y comunidad autonoma (valores absolutos y porcentajes) | Quarterly | Regional |

### Key Series Codes (Table 65194)

| Series Code | Description | Type |
|-------------|-------------|------|
| **EPA416255** | Asalariados. Total Nacional. Ambos sexos. Temporal: Total | Absolute (persons) |
| **EPA416256** | Asalariados. Total Nacional. Ambos sexos. Temporal: Total | Percentage |
| **EPA416257** | Temporal: Eventual por circunstancias de la produccion | Absolute |
| **EPA416259** | Temporal: De aprendizaje, formacion o practica | Absolute |
| **EPA416261** | Temporal: Estacional o de temporada | Absolute |
| **EPA416265** | Temporal: Cubrir la ausencia de otro trabajador | Absolute |
| **EPA416267** | Temporal: Para obra o servicio determinado | Absolute |

### Annual Summary Series (Table 10898)

| Series Code | Description |
|-------------|-------------|
| **MYH739** | Mujeres. Porcentaje asalariadas temporales respecto total asalariadas |
| **MYH740** | Mujeres. Porcentaje asalariadas temporales respecto total asalariados |
| **MYH741** | Hombres. Porcentaje asalariados temporales respecto total asalariados hombres |
| **MYH742** | Hombres. Porcentaje asalariados temporales respecto total asalariados |

### Calculation Note
To calculate the overall temporary contract rate:
```
Tasa de temporalidad = (Asalariados temporales / Total asalariados) * 100
```

---

## 5. Tasa de Parcialidad (Part-time Employment Rate)

Percentage of employed persons working part-time.

### Primary Tables

| Table ID | Table Name (Spanish) | Frequency | Coverage |
|----------|---------------------|-----------|----------|
| **65970** | Ocupados por tipo de jornada, sexo y grupo de edad | Quarterly | Current |
| **10896** | Porcentaje de los trabajadores a tiempo parcial en el empleo total | Annual | Summary indicator |
| **67552** | Porcentaje de trabajo a tiempo parcial de personas entre 20 y 64 anos por sexo y grupo de edad | Annual | EU indicator |
| **67559** | Porcentaje de trabajo a tiempo parcial de personas entre 20 y 64 anos por sexo y nivel de formacion | Annual | By education level |

### Key Series Codes (Table 65970)

| Series Code | Description | Type |
|-------------|-------------|------|
| **EPA640430** | Ocupados. Jornada completa. Total Nacional. Ambos sexos. 16+ anos | Absolute |
| **EPA640432** | Ocupados. Tiempo parcial. Total Nacional. Ambos sexos. 16+ anos | Absolute |
| **EPA640433** | Tasa de parcialidad. Total Nacional. Ambos sexos. 16+ anos | Percentage |
| **EPA640508** | Ocupados. Jornada completa. Total Nacional. Hombres | Absolute |
| **EPA640510** | Ocupados. Tiempo parcial. Total Nacional. Hombres | Absolute |
| **EPA640511** | Tasa de parcialidad. Total Nacional. Hombres | Percentage |
| **EPA640586** | Ocupados. Jornada completa. Total Nacional. Mujeres | Absolute |
| **EPA640588** | Ocupados. Tiempo parcial. Total Nacional. Mujeres | Absolute |
| **EPA640589** | Tasa de parcialidad. Total Nacional. Mujeres | Percentage |

### Annual Summary Series (Table 10896)

| Series Code | Description |
|-------------|-------------|
| **MYH8181** | Mujeres. Porcentaje tiempo parcial respecto total ocupadas |
| **MYH8182** | Mujeres. Porcentaje tiempo parcial respecto total ocupados |
| **MYH8183** | Hombres. Porcentaje tiempo parcial respecto total ocupados hombres |
| **MYH8184** | Hombres. Porcentaje tiempo parcial respecto total ocupados |

---

## 6. Paro Juvenil (Youth Unemployment Rate)

Unemployment rate for persons under 25 years old.

### Primary Tables

| Table ID | Table Name (Spanish) | Frequency | Coverage |
|----------|---------------------|-----------|----------|
| **14506** | Tasas de paro por distintos grupos de edad, sexo y comunidad autonoma | Quarterly | Historical |
| **65334** | Tasas de paro por distintos grupos de edad, sexo y comunidad autonoma | Quarterly | Current (2021 base) |
| **46554** | Tasas de paro por distintos grupos de edad, sexo y comunidad autonoma | Quarterly | Alternative |
| **67550** | Tasa de paro de personas entre 16 y 74 anos por sexo y grupo de edad | Annual | EU indicator |

### Key Series Codes (Table 14506)

| Series Code | Description |
|-------------|-------------|
| **EPA452436** | Tasa de paro. Total Nacional. Ambos sexos. Menos de 25 anos |
| **EPA452593** | Tasa de paro. Total Nacional. Hombres. Menos de 25 anos |
| **EPA452731** | Tasa de paro. Total Nacional. Mujeres. Menos de 25 anos |

### Regional Youth Unemployment (Selected)

| Series Code | Region |
|-------------|--------|
| **EPA452442** | Andalucia |
| **EPA452450** | Aragon |
| **EPA452458** | Asturias |
| **EPA452466** | Baleares |
| **EPA452474** | Canarias |

### Combined Rates Table (65349)

| Series Code | Description |
|-------------|-------------|
| **EPA453100** | Tasa de paro. Total Nacional. Ambos sexos |
| **EPA453220** | Tasa de paro. Total Nacional. Hombres |
| **EPA453340** | Tasa de paro. Total Nacional. Mujeres |

---

## 7. Empleo por Sectores (Employment by Economic Sector)

Employment breakdown by economic activity sector (CNAE classification).

### Primary Tables

| Table ID | Table Name (Spanish) | Frequency | Coverage |
|----------|---------------------|-----------|----------|
| **65123** | Ocupados por sexo y rama de actividad | Quarterly | National by sector |
| **65190** | Asalariados por sexo y rama de actividad | Quarterly | Employees only |

### Key Series Codes (Table 65123)

| Series Code | Description | Unit |
|-------------|-------------|------|
| **EPA397872** | Ocupados. Total Nacional. Ambos sexos. Total CNAE | Miles de personas |
| **EPA397873** | Ocupados. Total Nacional. Ambos sexos. Total CNAE | Porcentaje |

### Main Sector Categories (CNAE)

The table includes all CNAE economic divisions:
- Agriculture, forestry and fishing
- Mining and quarrying
- Manufacturing
- Electricity, gas, steam and air conditioning supply
- Water supply, sewerage, waste management
- Construction
- Wholesale and retail trade
- Transport and storage
- Accommodation and food service activities
- Information and communication
- Financial and insurance activities
- Real estate activities
- Professional, scientific and technical activities
- Administrative and support service activities
- Public administration and defence
- Education
- Human health and social work activities
- Arts, entertainment and recreation
- Other service activities
- Activities of households as employers
- Activities of extraterritorial organisations

Each sector has series for:
- Absolute numbers (persons)
- Percentages by sex

---

## API Usage Examples

### Fetch Table Metadata
```
GET https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/EPA
```

### Fetch Series from Table
```
GET https://servicios.ine.es/wstempus/js/ES/SERIES_TABLA/{TABLE_ID}
```

### Fetch Data for a Series
```
GET https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{SERIES_CODE}
```

### Fetch All Data from Table
```
GET https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{TABLE_ID}
```

### Example: Get Employment Rate Data
```python
import requests

# Fetch employment rate time series
url = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/EPA441060"
response = requests.get(url)
data = response.json()
```

---

## Data Notes

1. **Frequency:** All EPA tables are quarterly (trimestral)
2. **Units:**
   - Rates are expressed as percentages (%)
   - Absolute numbers are in thousands of persons (miles de personas)
3. **Base Year:** Current series use 2021 population base (changed April 2024)
4. **Historical Tables:** Tables with IDs starting with 4xxxx are often historical; newer tables (65xxx, 72xxx) use current methodology
5. **Regional Data:** Most indicators are available at national (Total Nacional), regional (Comunidad Autonoma), and provincial levels

---

## Quick Reference Summary

| Indicator | Primary Table | Key National Series |
|-----------|---------------|---------------------|
| Tasa de Empleo | 65305 / 65349 | EPA441060, EPA442577 |
| Tasa de Actividad | 65295 / 65349 | EPA388079, EPA438090 |
| Ocupados | 65109 | EPA387796 |
| Tasa de Temporalidad | 65194 / 10898 | EPA416255 (abs), EPA416256 (%) |
| Tasa de Parcialidad | 65970 / 10896 | EPA640433 |
| Paro Juvenil (<25) | 65334 / 14506 | EPA452436 |
| Empleo por Sectores | 65123 | EPA397872 |

---

## Sources

- [INE EPA Portal](https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736176918&menu=ultiDatos&idp=1254735976595)
- [INE API Documentation](https://www.ine.es/dyngs/DataLab/es/manual.html)
- [datos.gob.es EPA Datasets](https://datos.gob.es/es/catalogo?q=EPA)
