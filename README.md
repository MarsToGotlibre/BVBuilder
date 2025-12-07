# BVBuilder
 
BV Builder is a command-line tool designed to convert *Synchronized Skating* Scale of Value PDFs into clean, structured CSV and JSON files.

### Features
- Extracts Synchronized Skating Scale of Value data from ISU PDFs.
- Converts PDFs to structured CSV files.
- Builds multiple JSON formats ([GOE](#goe), [inline downgrades](#inline-downgrades), [reduction](#reduction-category), [large-output](#large-output)…)
- Modular pipeline: PDF ➞ CSV, CSV ➞ JSON, or full chain.
- Jupyter notebooks for customization.
- Example outputs are included.

### Content of this repository

 - **A CLI tool** for PDF and CSV parsing
 - **Jupyter notebooks** to understand or customize pipelines( [`Notebook/`](/Notebook/)
 )
 - **Example files** of CSV and JSON outputs [`examples/`](/examples/README.md) 

 ---
 
<details open>

<summary> <strong>Index</strong> </summary>

1. [Installation](#installation)
2. [CLI usage](#cli-usage)
    1. [PDF to CSV](#pdf-to-csv)
    2. [CSV to JSON](#csv-to-json)
    3. [Full Pipeline](#full-pipeline)
3. [Output](#output)
    1. [CSV output](#csv-output)
    2. [JSON output](#json-output)
        1. [GOE](#goe)
        2. [Reduction Category](#reduction-category)
        3. [Inline Downgrades](#inline-downgrades)
        4. [Large Output](#large-output)

</details>



## Installation
Requires:

- Python 3.10+
- Java 8+ (for tabula-py)
- Python dependencies : `pdfplumber`, `tabula-py`, `pandas`
```
pip install pdfplumber tabula-py pandas
```


# CLI usage
BVBuilder provides three subcommands for each pipeline:
- `pdftocsv` — extract CSV from the PDF
- `csvtojson` — build JSON from CSV
- `all` — full pipeline from PDF to JSON

### General use
```
python main.py <pipeline> <input file> [Options]
```

## PDF to CSV

### Command
```
python main.py pdftocsv <pdf_file> [-b BEGIN] [-e END] [-o OUTPUT]
```
### Arguments
| Option | Description|
| ----- | --------- |
| `-b, --begin`  | First Page |
| `-e, --end`  | Last page (optional)|
| `-o, --output` | Output file name (optional) |

### Notes :
- If end page not specified, **only the begin page is processed**
- If no output entered, BVbuilder generates one automatically : 
```
pdf_example-page-1.csv
pdf_example-page-(3-6).csv
```
### Examples :
```
python main.py pdftocsv pdf_example.pdf -b 4 -e 6
```
Output : `pdf_example-page-(4-6).csv` 

##  CSV to JSON

### Command :
```sh
python main.py csvtojson <csv_file> [options]
```

### Arguments

| Option                     | Description   | ex|
| -------------------------- | ------------- | ----|
| `-l, --large-output`       | **Exclusive mode.** Produces one JSON entry per CSV row. Can't be combined with other options.      |[#](#large-output)|
| `-i, --inline-downgrades`  | Places downgrade values directly inside each element level instead of in a separate structure.      |[#](#inline-downgrades)|
| `-c, --reduction-category` | Groups elements of a category into a single category entry if they have the same value.             |[#](#reduction-category)|
| `-g, --goe`                | Includes GOE values in the output JSON.                                                             |[#](#goe) |
| `-s, --synchro-skate-calc` | Generation of the SynchroSkateCalc JSON. Currently equivalent to `--reduction-category`.    ||
| `-o, --output OUTPUT`      | Output JSON filename (optional).                                                                    ||




## Full pipeline

```
python main.py all <pdf_file> -b BEGIN -e END --temp-csv temp.csv [other json options]
```
This command runs the entire processing pipeline:

- PDF 🠖 CSV
- CSV 🠖 JSON

The available options are the same as in the two separate commands (`pdftocsv` and `csvtojson`).

### Temporary CSV handling

During the process, BVBuilder automatically generates a CSV file.
This is useful because the PDF extraction step is the most resource-intensive part (due to the use of Java though `tabula-py`).
Keeping a CSV backup ensures you don’t need to re-process the PDF if something goes wrong during JSON generation.

You can choose the name of this temporary file using the `--temp-csv` option.

### Note

The CSV file is not deleted automatically after JSON generation.
You may remove it manually if you no longer need it.

# Output

## CSV output 


| Column | Description | Info | 
| - | - | ---- |
|`Category`|The category the element is in|Some element are listed under a category with this Format : ***ARTISTIC ELEMENTS - Artistic Block (AB)***. This Columns stores "***ARTISTIC ELEMENTS***". If the Element doesnt have  a category, the element name is used to fill this.|
|`ElmtName`|Element Name|To take the same example, here it could be "**Artistic Block**"|
|`Levels`|Level shown in the PDF|Includes the level contributed by the Additional Feature. This differs from `ElmtLvl`.|
|`ElmtNot`|Element Notation|Symbol+level+downgrade string as written in the PDF.|
|`Element`|Element symbol |Extracted from `ElmtNot`. For Example if `ElmtNot` = `ME3`, this column would contain `ME`.|
|`ElmtLvl`|Element Level|Pure element level for element like `I3+pi2`, this would be equal to `3`|
|`AFNot`|Additional feature notation|Additinal Feature column in the pdf|
|`-5, -4, -3, -2, -1, 1, 2, 3, 4` and `5`|GOE values|GOE columns extracted from the PDF tables.|
|`BASE`|Element Base value|---|
|`DGrade`| Downgrade count|0 = none, 1 = `<`, 2 = `<<`.|
|`AddFeat`|Additional feature symbol|---|
|`AFLvl`|Additional Feature Level|---|

## JSON Output

The default JSON structure is :
```json
{
  "Element": {
    "ElmntLvl": /* BASE */
  },
  "Element":{
    "ElmtLvl":{
      "AddFeat": /* BASE */
    }
  },
  "Downgrades":{
    "<":/* value */,
    "<<":/* value */
  }
}
```
`/*BASE*/` Being the value of the CSV `BASE` column.

By using options you will modify the structure as follows :

---

### GOE
**Command** : `--goe,-g`  
Insead of just the `BASE` column the end will be provided with more detailed tree including the goe values.  
What is added :
```json
{
  "base":/*BASE*/
  "goe":{
    "-5": /*...*/,
    "-4": /*...*/,
    "-3": /*...*/,
    "-2": /*...*/,
    "-1": /*...*/,
    "BASE": /*...*/,
    "1": /*...*/,
    "2": /*...*/,
    "3": /*...*/,
    "4": /*...*/,
    "5": /*...*/
  }
}
```

### Inline Downgrades
**Command** : `--inline-downgrades, -i`   
Places downgrades values directly inside each element level instead of in a separate structure. 
This Creates the following structure :
```json
{
  "Element": {
    "ElmtLvl": {
      "NoDg": /* BASE */,
      "<": /* BASE */,
      "<<": /* BASE */
    }
  }
}

```

|Key|DGrade|Meaning|
|--------- |---------|------------|
|`"NoDg"`| `0` | No downgrade|
|`"<"`| `1` | One downgrades|
|`"<<"`| `2` | Two downgrades|

If no downgrades are found for a given level, only the `"NoDg"` entry will be added in the JSON.
### Reduction Category
**Command** : `--reduction-category, -c`  
Groups multiple elements into a single category entry if they share the same base/GOE values.
Here's an Example with `Artistic Elements`
#### Before :
```json
{
  "AB":{},
  "AC":{},
  "AL":{},
  "AW":{}
}
```
#### After
```json
{
  "A": {}
}
```
If no prefix exists (like the `A` here), the `Category` column will be used instead.

### Large Output
**Command** : `--large-output, -l`  
This is the only option that doesn't respect this pattern. Here's an example :
```json
{
  "ME3<": {
    "base": 3.0,
    "goe": { /* GOE values */ }
  },
  "I2-pi1": {
    "base": 2.5,
    "goe": { /* ... */ }
  }
}
```
This output resembles the result of the `--goe` option.
