import pandas as pd
import json
from src.pdf_to_csv import GOE
import logging
logger = logging.getLogger(__name__)

class Config:
    def __init__(self, largeOutput=False, inline_downgrades=False, reductionCategory=False, goe=False):
        self.largeOutput = largeOutput
        self.inline_downgrades = inline_downgrades
        self.reductionCategory = reductionCategory
        self.goe = goe
    
    @classmethod
    def synchro_skate_calc(cls):
        return cls(False,False,True,False)
    
    def inline_dg(self,value:bool):
        self.inline_downgrades=value

### -------------- Are Category Equal--------------------

def FindCategoryofElements(df,categorylist): #=df["Category"].unique()
    List=[]
    for category in categorylist:
        Cat=df.query(f"Category == '{category}'")["Element"].unique()
        if len(Cat)>1:
            List.append({"Category":category,"Elements":Cat})
    return List

def CategoryEqual(df,ListElem):
    temp=df.query(f"ElmtName == '{ListElem[0]}'")[GOE]
    for i in range(1,len(ListElem)):
        elem=df.query(f"ElmtName == '{ListElem[i]}'")[GOE]
        if not elem.reset_index(drop=True).equals(temp.reset_index(drop=True)): # if the Two dataframes are different
            return False
        else:
            temp=elem
    return True

#----------- Are Downgrades Equal---------------------

def findDGval(df):
    try :
        rowdg1=df.query("DGrade == 1").iloc[0]
        rowdg2=df.query("DGrade == 2").iloc[0]
        row1=df.query(f"Element == '{rowdg1["Element"]}' and ElmntLvl == '{rowdg1["ElmntLvl"]}' and DGrade == 0")
        row2=df.query(f"Element == '{rowdg2["Element"]}' and ElmntLvl == '{rowdg2["ElmntLvl"]}' and DGrade == 0")
        return ((row1["BASE"]-rowdg1["BASE"]).iloc[0],(row2["BASE"]-rowdg2["BASE"]).iloc[0])
    except Exception as e:
        logger.warning(f"find Downgrade Value Failed : {e}")
        return None

def DowngradesValueEqual(df,dg): #=findDGval(df)
    dgdf=df.query("DGrade != 0")
    for tup in dgdf.itertuples():
        temp=(df.query(f"Element == '{tup.Element}' and ElmntLvl == '{tup.ElmntLvl}' and DGrade == 0")["BASE"]-tup.BASE).iloc[0]
        if not dg[tup.DGrade-1]==temp:
            return False
    return True


# -------------- Create the Dictionnary (futur json)

def outputValue(tup,config:Config):
    if config.goe:
        return {"base":tup.BASE,"goe":dict(zip(GOE,tup[7:18]))}
    else :
        return tup.BASE


def DowngradeKey(DowngradeValue):
    return "NoDg" if DowngradeValue==0 else DowngradeValue*"<"

def fillElement(elementGroup,config:Config,element):
    
    #Without Additional Feature
    if elementGroup["AFNot"].isna().all():
        if not config.inline_downgrades:
            for Lvl in elementGroup.itertuples():
                element[Lvl.ElmntLvl]=outputValue(Lvl,config)
        else:
            for LvlElem,GroupLvl in elementGroup.groupby("ElmntLvl"):
                element[LvlElem]={}
                for Dg in GroupLvl.itertuples():
                    key=DowngradeKey(Dg.DGrade)
                    element[LvlElem][key]=outputValue(Dg,config)
   #with additional Feature                 
    else:
        if not config.inline_downgrades:
            for LvlElem,GroupLvl in elementGroup.groupby('ElmntLvl'):
                element[LvlElem]={}
                for AddF in GroupLvl.itertuples():
                    element[LvlElem][AddF.AFNot]=outputValue(AddF,config)
        else:
            for LvlElem,GroupLvl in elementGroup.groupby("ElmntLvl"):
                element[LvlElem]={}
                for AddF,GroupAF in GroupLvl.groupby("AFNot"):
                    element[LvlElem][AddF]={}
                    for Dg in GroupAF.itertuples():
                        key=DowngradeKey(Dg.DGrade)
                        element[LvlElem][AddF][key]=outputValue(Dg,config)

### ---------------------- Option -----------------------------------

def LargeJson(df):
    element={}
    for row in df.itertuples():
        if pd.isna(row.AFNot) or row.AFNot =="-":
            element[row.ElmtNot]={"base":row.BASE,"goe":dict(zip(GOE,row[7:18]))}
        else :
            element[row.ElmtNot+"+"+row.AFNot]={"base":row.BASE,"goe":dict(zip(GOE,row[7:18]))}
    return element

def reductionCategory(df,dictElement,config:Config):
    cat=FindCategoryofElements(df,df["Category"].unique())
   
    if  not config.inline_downgrades:
        query="DGrade == 0"
        tempdf = df.query(query)
    else:
        query=""
        tempdf=df
    for i in range(len(cat)):
        equal=CategoryEqual(tempdf,cat[i]["Elements"])
        if equal:
            
            # Définir les noms des éléménts du json
            name=cat[i]["Elements"][0][:-1] if len(cat[i]["Elements"][0])>1 else cat[i]["Category"]

            #Création du nom dans le dictionnaire
            dictElement[name]={}
            fillElement(tempdf.query(f"Element == '{cat[i]["Elements"][0]}'"),config,dictElement[name])
            
            if len(query)>0:
                query+= f" and Category != '{cat[i]['Category']}'"
            else :
                query+= f"Category != '{cat[i]['Category']}'"
    return query

### ----------------------- Json Implementation -----------------------

def returnDict(df,config:Config):
    if config.largeOutput:
        
        return LargeJson(df)
    
    dictElement={}
    dg=findDGval(df)
    query=""
    if dg!=None :
        if not DowngradesValueEqual(df,dg) :
            logger.info("Downgrades values aren't equal")
            if config.inline_dg == False :
                config.inline_dg(True)
                logger.warning("Inline downgrade option will be applied")

        
        if not config.inline_downgrades:
            dictElement["Downgrades"]=dict(zip(["<","<<"],dg))
            query="DGrade == 0"
            logger.info("Downgrades Separated")

    if config.reductionCategory:
        query=reductionCategory(df,dictElement,config)
        logger.info("Category reducted")
    
    iterDf= df.query(query) if query else df
    
    for elem,group in iterDf.groupby('Element'):
        dictElement[elem]={}
        fillElement(group,config,dictElement[elem])
    logger.info("Json structure finished")
    return dictElement

# ------------------ Write Json --------------------------------

def returnJsonFile(input,config:Config,output):
    df=pd.read_csv(input)
    JsonDict=returnDict(df,config)
    with open(output,"w") as f :
        json.dump(JsonDict,f,indent=4)
    logger.info(f"Json genrerated in : {output}")