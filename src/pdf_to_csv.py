import pdfplumber
import pandas as pd
import tabula
import re
import logging
logger = logging.getLogger(__name__)


minColumns=13
GOE=[str(i) for i in range(-5,0)]+["BASE"]+[str(i) for i in range(1,6)]
Header=["Levels","ElmtNot","AFNot"]+GOE
nbrCol=14

### --------------------- Title Extraction -----------------------------------
class PDFLoader:
    def __init__(self, filename):
        try:
            self.pdf = pdfplumber.open(filename)
        except Exception as e:
            raise RuntimeError(f"Unable to open PDF {filename}: {e}")
        self.filename=filename

    def get_page_lines(self, pagenumber):
        try:
            page = self.pdf.pages[pagenumber - 1]
            return page.extract_text_lines(return_chars=False)
        except IndexError:
            logger.error(f"Page {pagenumber} does not exist")
            return None
        except Exception as e:
            logger.error(f"Error on page {pagenumber}: {e}")
            return None
    
    def get_all_pages_lines(self,beginpage,endpage):
        lines = []
        for page in range(beginpage, endpage +1):
            lines+= self.pdf.pages[page-1].extract_text_lines(return_chars=False)
        return lines

    def close(self):
        self.pdf.close()


class Element:
    def __init__(self, Category, Element, Symbol):
        self.Category = Category
        self.Element = Element
        self.Symbol = Symbol

pattern = re.compile(
    r"""
    ^(?:\d+\.\s*)?              # optional Number (ex: "1. ")
    ([A-Z ]+?)                  # Main category (ex: "ARTISTIC ELEMENT")
    (?:\s*-\s*([A-Za-z ]+))?    # sub-element after "-" (ex: "Artistic Block")
    (?:\s*\(([A-Za-z]+)\))?     # symbol between parenthesis (ex: "AB")
    $""",
    re.VERBOSE
)

def FindElementName(lines):
    ListeElem=[]
    Groupe=""
    for line in lines:
        m = pattern.match(line["text"].strip())
        if m:
            cat, sub, sym = m.groups()
            if not sym:
                logger.debug(f"Group pattern Found : {cat}")
                Groupe=cat
            
            else:
                if sub :
                    
                    if Groupe:
                        logger.debug("\t Sub Pattern found : " , sub)
                        ListeElem.append(Element(Groupe,sub,sym))
                    else:
                        logger.debug("\t Sub patttern whitout group announced : " , sub)
                        ListeElem.append(Element(cat,sub,sym))
                    
                else:
                    logger.debug("Simple element found", cat)
                    ListeElem.append(Element(cat,cat,sym))
    return ListeElem


### -------------------------Find and associate tables --------------------------------


def return_all_tables(filename,beginpage,endpage):
    pages=[i for i in range (beginpage,endpage +1)] 
    ListTable=tabula.read_pdf(filename, pages=pages,pandas_options={"header":None},guess=True,columns=[250,450,640,830,940,1050,1160,1270,1380,1490,1600,1710,1820,1930,2040])
    return ListTable

def CleanNonElementsTable(pagedf):
    i=0
    logger.info("Verifing if all df are the right size")
    while i < len(pagedf):

        if pagedf[i].shape[1]<minColumns:           
            pagedf.pop(i)
            logger.debug(f"table number {i} removed")
            logger.debug(f"Element number {i+1} and after are falling in {i}")
            i-=1
        i+=1
    logger.info("Verification done")

def TitleAsManyTable(dfs,TitleList):
    if len(dfs)!=len(TitleList):
        logger.warning("Error, not as many title as tables")
        logger.warning(f"{len(dfs)} dataframes while  having {len(TitleList)} Titles")
        return False
    else :
        return True

def CleanNaNLines(dfs):
    for i in range(len(dfs)):
        if dfs[i].isna().all(axis=1).any():
            logger.debug(f"nan line found  in number {i} dataframe ")
            dfs[i]=dfs[i].dropna(how="all")
        else:
            logger.debug(f"no nan found in number {i} dataframe")

def SetColumns(dfs,Columns=nbrCol):
    for df in dfs:
        if df.shape[1]<Columns:
            df.insert(loc=2, column='new', value=pd.NA) ##Additional Feature
            logger.debug(f"one table size {df.shape[1]} resized to {Columns}")

def SetColumnName(dfs):
    for df in dfs:
        if df.shape[1]!=nbrCol: ## NOMBRE VARIBLE COLONNES
            logger.warning("One dataframe isn't the right size, return")
        else:
            df.columns=Header

def TableAsso(dfs,ListElem):
    indexList=0
    for df in dfs:
        df.insert(loc=2, column="Element", value=ListElem[indexList].Symbol)
        df.insert(loc=0, column="ElmtName",value=ListElem[indexList].Element)
        df.insert(loc=0, column="Category",value=ListElem[indexList].Category)
        indexList+=1

def VerifyAsso(dfs):
    Associated=True
    for i in range(len(dfs)):
        df=dfs[i]
        if df["ElmtNot"][0][:-1]!=df["Element"][0]: # Always Elem Lvl B
            logger.error(f"Something whent wrong with association : {df["ElmtNot"][0][:-1]} is not {df["Element"][0]}")
            Associated=False
    if not Associated:
        logger.info("Association went right")
    return Associated


### ----------- Adding Completing dataframe info ------------------------

def AddDowngrades(df):
    df["DGrade"]=df["ElmtNot"].astype(str).str.count("<").fillna(0).astype(int)
    logger.info("Downgrades column added")

def LevelComplete(df):
    logger.info("Verifying if all Levels are There")

    if df["Levels"].isna().any():
        logger.info("NaN entries in Levels found")
        df["Levels"] = df["Levels"].ffill()
        
        if not df["Levels"].isna().any():
            logger.info("Completion done")
        else:
            logger.warning("Something went wrong with completion")
    else:
        logger.info("Levels There")


# Adds a columns for the element Lvl. Different than column "Levels". 
# Ex = Level 14,I3,piB --> ElmntLvl = 3

def ExtractElementLvl(df):
    s=df["ElmtNot"]
    n=df["DGrade"]
    if n==0:
        return s[-1:]
    else:
        return s[-n-1:-n]

def ElementLvl(df):
    df["ElmntLvl"]=df.apply(ExtractElementLvl,axis="columns")
    logger.info("Element Level Added")


#Creates a clumn like "Element" and "ElmntLvl" for the Additional Feature. 
# Ex : pi3 --> "AddFeat"=pi,"AFLvl"=3
def ExtractFeat(val):
    if pd.isna(val) or val == "-":
        return (val, pd.NA)
    return (val[:-1], val[-1:])

def AddFeat(df):
    df[["AddFeat", "AFLvl"]] = df["AFNot"].apply(ExtractFeat).apply(pd.Series)
    logger.info("Additional Feature Added")


### --------------------------- Dataframe Build ------------------------------------


def all_pages_into_df(pdfLoader:PDFLoader,beginpage,endpage):
    lines=pdfLoader.get_all_pages_lines(beginpage,endpage)
    pdfLoader.close()
    ListElem=FindElementName(lines)
    dfs=return_all_tables(pdfLoader.filename,beginpage,endpage)
    
    CleanNonElementsTable(dfs)
    if TitleAsManyTable(dfs,ListElem):
        CleanNaNLines(dfs)
        
        SetColumns(dfs)
        SetColumnName(dfs)
        TableAsso(dfs,ListElem)

    else:
        logger.warning("Not as Many Element as tables")
        return 
    return dfs

def GOEtoFloat(df):
    df[GOE] = df[GOE].apply(lambda x: x.str.replace(',', '.').astype(float) if x.dtype == 'object' else x)
    logger.info("GOE turned into Float")

def DfLvlAndDowngradest(df):
    
    AddDowngrades(df)
    LevelComplete(df)

    ElementLvl(df)
    AddFeat(df)

    GOEtoFloat(df)


def extrat_document(filename,beginpage,endpage):
    pdfloader=PDFLoader(filename)
    DfList=all_pages_into_df(pdfloader,beginpage,endpage)
    if VerifyAsso(DfList):
        return DfList
    else:
        raise IndexError("Something whent wrong with association")

def CreateCSV(filename,beginpage,endpage,outputfilename):
    DFList=extrat_document(filename,beginpage,endpage)
    BigDf=pd.concat(DFList,ignore_index=True)
    DfLvlAndDowngradest(BigDf)
    
    BigDf.to_csv(outputfilename)
    logger.info(f"Created csv : {outputfilename}")
    

