import argparse
from pathlib import Path
from src.pdf_to_csv import CreateCSV
import logging

logging.basicConfig(
    level=logging.INFO,       
    format="[%(levelname)s] - %(message)s"
)


class ConfigJson:
    def __init__(self,LargeOutput,SeparateDowngrades,ReductionCategory,GOE):
        self.LargeOutput =LargeOutput
        self.SeparateDowngrades=SeparateDowngrades
        self.ReductionCategory= ReductionCategory
        self.GOE = GOE


def build_parser():
    parser = argparse.ArgumentParser(
        description="Pipeline: PDF → CSV → JSON"
    )
    subparsers = parser.add_subparsers(dest="pipeline", required=True)

    # PARENT: options CSV → JSON
    json_parent = argparse.ArgumentParser(add_help=False)
    json_parent.add_argument("-l", "--large-output", action="store_true")
    json_parent.add_argument("-d", "--separate-downgrades", action="store_true")
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
    json_parser.add_argument("-o", "--output", default="output.json")

    # ---------- FULL PIPELINE ----------
    all_parser = subparsers.add_parser("all", parents=[csv_parent,json_parent],help="PDF → CSV → JSON")
    
    all_parser.add_argument("pdf_file")
    all_parser.add_argument("--temp-csv")
    all_parser.add_argument("-o", "--json-output", default="output.json")

    return parser



def check_file_exists(path):


    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    #return path

def check_extention(path,allowed_ext):
    logging.debug(f"{path.suffix.lower()}")
    if path.suffix.lower() != allowed_ext:
        raise ValueError(f"Invalid file type: {path.suffix}. Expected one of: {allowed_ext}")

def check_output_file(str_path,allowed_ext):
    path=Path(str_path)
    check_extention(path,allowed_ext)

def name(args):
    name=""
    if args.large_output:
        return"-large_output"
    if args.synchro_skate_calc:
        name+="-synchro_skate_calc"
    if args.separate_downgrades:
        name+="-separate_downgrades"
    if args.reduction_category:
        name+="-reduction_category"
    if args.goe:
        name+="-goe"
    return name


def pdf_to_cscv(args):
    path=Path(args.pdf_file)
    
    check_file_exists(path)
    check_extention(path,".pdf")
    
    if args.end is None :
        args.end=args.begin

    if args.output!=None :
            check_extention(Path(args.output),".csv")
    else :
        args.output = f"{path.stem}-page-{str(args.begin)if args.begin==args.end else "("+str(args.begin)+"-"+str(args.end)+")"}.csv"
    
    print(args.pdf_file,args.begin,args.end,args.output)
    #CreateCSV(args.pdf_file,args.begin,args.end,args.output)
    return args.output

def csv_to_json(args):
    path=Path(args.csv_file or args.temp_csv)

    check_file_exists(path)
    check_extention(path,".csv")
    if args.output!=None :
            check_extention(Path(args.output),".json")
    else :
        args.output = f"{path.stem}{name(args)}.json"
        logging.debug(args.output)

    


 


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    print()
    
    print(args)
    print()
    #pdf_to_cscv(args)
    
    print()
    print(args)
