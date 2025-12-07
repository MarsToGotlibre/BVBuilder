import argparse
from pathlib import Path
from src.pdf_to_csv import CreateCSV
from src.csv_to_json import returnJsonFile,Config
import logging

logger = logging.getLogger(__name__)

def build_parser():
    parser = argparse.ArgumentParser(
        description="Pipeline: PDF → CSV → JSON"
    )
    subparsers = parser.add_subparsers(dest="pipeline", required=True)

    # PARENT: options CSV → JSON
    json_parent = argparse.ArgumentParser(add_help=False)
    json_parent.add_argument("-l", "--large-output", action="store_true")
    json_parent.add_argument("-i", "--inline_downgrades", action="store_true")
    json_parent.add_argument("-c", "--reduction-category", action="store_true")
    json_parent.add_argument("-g","--goe",action="store_true")
    json_parent.add_argument("-s", "--synchro-skate-calc", action="store_true")

    # PARENT: options PDF -> CSV
    csv_parent=argparse.ArgumentParser(add_help=False)
    csv_parent.add_argument("-b", "--begin", type=int,default=3)
    csv_parent.add_argument("-e", "--end", type=int)

    # ---------- PDF → CSV ----------
    pdf_parser = subparsers.add_parser("pdftocsv", parents=[csv_parent], help="Convert PDF to CSV")

    pdf_parser.add_argument("pdf_file")
    pdf_parser.add_argument("-o", "--output")

    # ---------- CSV → JSON ----------
    json_parser = subparsers.add_parser("csvtojson", parents=[json_parent], help="Convert CSV to JSON")

    json_parser.add_argument("csv_file")
    json_parser.add_argument("-o", "--output")

    # ---------- FULL PIPELINE ----------
    all_parser = subparsers.add_parser("all", parents=[csv_parent,json_parent],help="PDF → CSV → JSON")
    
    all_parser.add_argument("pdf_file")
    all_parser.add_argument("--temp-csv")
    all_parser.add_argument("-o", "--output")

    return parser

def init_logging(level: str="INFO")-> logging.Logger:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="[%(levelname)s] %(name)s - %(message)s"
    )

def check_file_exists(path):


    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    #return path

def check_extention(path,allowed_ext):
    logger.debug(f"{path.suffix.lower()}")
    if path.suffix.lower() != allowed_ext:
        raise ValueError(f"Invalid file type: {path.suffix}. Expected one of: {allowed_ext}")

#def check_output_file(str_path,allowed_ext):
#    path=Path(str_path)
#    check_extention(path,allowed_ext)

def name(args):
    name=""
    if args.large_output:
        return"-large_output"
    if args.synchro_skate_calc:
        return"-synchro_skate_calc"
    if args.inline_downgrades:
        name+="-inline_downgrades"
    if args.reduction_category:
        name+="-reduction_category"
    if args.goe:
        name+="-goe"
    return name

def jsonConfig(args):
    if args.synchro_skate_calc:
        return Config.synchro_skate_calc()
    return Config(args.large_output,args.inline_downgrades,args.reduction_category,args.goe)

def pdf_to_csv(args):
    path=Path(args.pdf_file)
    
    check_file_exists(path)
    check_extention(path,".pdf")
    
    if args.end is None :
        args.end=args.begin

    output="output" if args.pipeline=="pdftocsv" else "temp_csv"
    if getattr(args,output)!=None :
            check_extention(Path(getattr(args,output)),".csv")
    else :
        setattr(args,output,f"{path.stem}-page-{str(args.begin)if args.begin==args.end else "("+str(args.begin)+"-"+str(args.end)+")"}.csv") 
    #print(args.pdf_file,args.begin,args.end,getattr(args,output))
    CreateCSV(args.pdf_file,args.begin,args.end,getattr(args,output))
    #return getattr(args,output)

def csv_to_json(args):
    path=Path(args.csv_file if args.pipeline=="csvtojson" else args.temp_csv)

    check_file_exists(path)
    check_extention(path,".csv")
    if args.output!=None :
            check_extention(Path(args.output),".json")
    else :
        args.output = f"{path.stem}{name(args)}.json"
        logger.debug(args.output)

    returnJsonFile(path,jsonConfig(args),args.output)

def pdf_to_json(args):
    pdf_to_csv(args)
    csv_to_json(args)

def init_pipeline(args):
    match args.pipeline:
        case "pdftocsv":
            pdf_to_csv(args)
        case "csvtojson":
            csv_to_json(args)
        case "all":
            pdf_to_json(args)
 


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    init_logging()

    init_pipeline(args) 
