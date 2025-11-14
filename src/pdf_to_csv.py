import pdfplumber
import pandas as pd
import tabula
import re
import logging

logging.basicConfig(
    level=logging.INFO,       
    format="%(levelname)s - %(message)s"
)


minColumns=13
GOE=[str(i) for i in range(-5,0)]+["BASE"]+[str(i) for i in range(1,6)]
Header=["Levels","ElmtNot","AFNot"]+GOE
nbrCol=14

### --------------------- Title Extraction -----------------------------------

def returnPageLines(filename,pagenumber):
    pdf = pdfplumber.open(filename)
    page = pdf.pages[pagenumber-1]
    return page.extract_text_lines(return_chars=False)

def Element(Category,Element,Symbol):
    Dictionnaire={
        "Category":Category,
        "Element":Element,
        "Symbol":Symbol
    }
    return Dictionnaire

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
                logging.debug(f"Group pattern Found : {cat}")
                Groupe=cat
            
            else:
                if sub :
                    
                    if Groupe:
                        logging.debug("\t Sub Pattern found : " , sub)
                        ListeElem.append(Element(Groupe,sub,sym))
                    else:
                        logging.debug("\t Sub patttern whitout group announced : " , sub)
                        ListeElem.append(Element(cat,sub,sym))
                    
                else:
                    logging.debug("Simple element found", cat)
                    ListeElem.append(Element(cat,cat,sym))
    return ListeElem


### -------------------------Find and associate tables --------------------------------

def returnTablesFromPage(filename,pagenumber):
    return tabula.read_pdf(filename, pages=pagenumber,pandas_options={"header":None})

def CleanNonElementsTable(pagedf):
    i=0
    logging.info("Verifing if all df are the right size")
    while i < len(pagedf):

        if pagedf[i].shape[1]<minColumns:           
            pagedf.pop(i)
            logging.debug(f"table number {i} removed")
            logging.debug(f"Element number {i+1} and after are falling in {i}")
            i-=1
        i+=1
    logging.info("Verification done")

def TitleAsManyTable(dfs,TitleList):
    if len(dfs)!=len(TitleList):
        logging.error("Error, not as many title as tables")
        logging.error(f"{len(dfs)} dataframes while  having {len(TitleList)} Titles")
        return False
    else :
        return True

def CleanNaNLines(dfs):
    for i in range(len(dfs)):
        if dfs[i].isna().all(axis=1).any():
            logging.debug(f"nan line found  in number {i} dataframe ")
            dfs[i]=dfs[i].dropna(how="all")
        else:
            logging.debug(f"no nan found in number {i} dataframe")

def SetColumns(dfs,Columns=nbrCol):
    for df in dfs:
        if df.shape[1]<Columns:
            df.insert(loc=2, column='new', value=pd.NA) ##Additional Feature
            logging.debug(f"one table size {df.shape[1]} resized to {Columns}")

def SetColumnName(dfs):
    for df in dfs:
        if df.shape[1]!=nbrCol: ## NOMBRE VARIBLE COLONNES
            logging.warning("One dataframe isn't the right size, return")
            return
        else:
            df.columns=Header

def TableAsso(dfs,ListElem):
    indexList=0
    for df in dfs:
        df.insert(loc=2, column="Element", value=ListElem[indexList]["Symbol"])
        df.insert(loc=0, column="ElmtName",value=ListElem[indexList]["Element"])
        df.insert(loc=0, column="Category",value=ListElem[indexList]["Category"])
        indexList+=1

def VerifyAsso(dfs):
    Associated=True
    for i in range(len(dfs)):
        df=dfs[i]
        if df["ElmtNot"][0][:-1]!=df["Element"][0]: # Always Elem Lvl B
            logging.error(f"Something whent wrong with association : {df["ElmtNot"][0][:-1]} is not {df["Element"][0]}")
            Associated=False
    if not Associated:
        logging.info("Association went right")
    return Associated


### ----------- Adding Completing dataframe info ------------------------

def AddDowngrades(df):
    df["DGrade"]=df["ElmtNot"].astype(str).str.count("<").fillna(0).astype(int)

def LevelComplete(df):
    logging.info("Verifying if all Levels are There")

    if df["Levels"].isna().any():
        logging.info("NaN entries in Levels found")
        df["Levels"] = df["Levels"].ffill()
        
        if not df["Levels"].isna().any():
            logging.info("Completion done")
        else:
            logging.warning("Something went wrong with completion")
    else:
        print("Levels There")


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


#Creates a clumn like "Element" and "ElmntLvl" for the Additional Feature. 
# Ex : pi3 --> "AddFeat"=pi,"AFLvl"=3
def ExtractFeat(val):
    if pd.isna(val) or val == "-":
        return (val, pd.NA)
    return (val[:-1], val[-1:])

def AddFeat(df):
    df[["AddFeat", "AFLvl"]] = df["AFNot"].apply(ExtractFeat).apply(pd.Series)


### --------------------------- Dataframe Build ------------------------------------

def pageIntoListDf(filename,page):
    lines=returnPageLines(filename,page)
    ListElem=FindElementName(lines)

    dfs=returnTablesFromPage(filename,page)
    
    CleanNonElementsTable(dfs)
    if TitleAsManyTable(dfs,ListElem):
        CleanNaNLines(dfs)
        
        SetColumns(dfs)
        SetColumnName(dfs)
        TableAsso(dfs,ListElem)

    else:
        logging.warning("Not as Many Element as tables")
        return 
    return dfs

def GOEtoFloat(df):
    df[GOE] = df[GOE].apply(lambda x: x.str.replace(',', '.').astype(float) if x.dtype == 'object' else x)

def DfLvlAndDowngradest(df):
    
    AddDowngrades(df)
    LevelComplete(df)

    ElementLvl(df)
    AddFeat(df)

    GOEtoFloat(df)

def ExtractDocumentperPage(filename,beginpage,endpage):
    DfList=[]
    for page in range(beginpage,endpage+1):
        pageList=pageIntoListDf(filename,page)
        if VerifyAsso(pageList):
            DfList+=pageList
    return DfList

def CreateFinalDf(filename,beginpage,endpage,outputfilename):
    DFList=ExtractDocumentperPage(filename,beginpage,endpage)
    BigDf=pd.concat(DFList,ignore_index=True)
    DfLvlAndDowngradest(BigDf)
    
    BigDf.to_csv(outputfilename)
    

