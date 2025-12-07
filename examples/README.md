# Exemples
This folder contains example files generated from the same source PDF, using different pipeline options.

These examples show the typical input/output flow of **pdftocsv** and **csvtojson**.



## PDF to CSV
**Input File** : `ISU-2693-ISU-SYS-SOV.pdf` (All Scale of Value data is located on pages 3 to 6.)   
**Pipeline** : `pdftocsv`

| Output file| Arguments | Description |
|--|--|--|
|`ISU-2693-ISU-SYS-SOV-page-(3-6).csv` |  `-b 3 -e 6` | Extract pages 3 to 6|



## CSV to JSON

**Input File** : `ISU-2693-ISU-SYS-SOV-page-(3-6).csv`  
**Pipeline** : `csvtojson`

| Output file| Arguments | Description |
|--|--|--|
|`ISU-2693-ISU-SYS-SOV-page-(3-6).json` |  None | Default JSON output (see [Json output](../README.md#json-output))|
|`ISU-2693-ISU-SYS-SOV-page-(3-6)-reduction_category.json` | `-r` | [Reduction category](../README.md#reduction-category) |
|`ISU-2693-ISU-SYS-SOV-page-(3-6)-large_output.json` | `-l` | [Large output](../README.md#large-output) |
|`ISU-2693-ISU-SYS-SOV-page-(3-6)-goe.json` | `-g` | [Includes GOE](../README.md#goe) |
|