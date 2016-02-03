#!/usr/bin/env python
# -*- coding: utf-8 -*

import urllib.request
import datetime
import xml.etree.ElementTree as ET


class Scraper(object):

    def __init__(self):
        self.root = "http://www.kansalliskirjasto.fi/extra/marc21/bib/"
        self.urls = ["001-006.xml", "007.xml", "008.xml", "01X-04X.xml", "05X-08X.xml", "1XX.xml", "20X-24X.xml",
                     "250-270.xml", "3XX.xml", "4XX.xml", "50X-53X.xml", "53X-58X.xml", "6XX.xml", "70X-75X.xml",
                     "76X-78X.xml", "80X-830.xml", "841-88X.xml", "9XX.xml", "omat.xml"]

    def readData(self):
        data = []
        for x in self.mapUrls():
            data.append(ET.fromstring(urllib.request.urlopen(x).read()))
        return data

    def mapUrls(self):
        return map(lambda x: self.root + x, self.urls)


class Parser(object):

    def __init__(self, data):
        self.data = data
        self.parsedData = {}

    def parseData(self):
        for xmlFile in self.data:
            for x in xmlFile:
                if (x.tag == "controlfields"):
                    self.parseControlField(x)
                elif (x.tag == "datafields"):
                    self.parseDataField(x)

    def parseDataField(self, field):
        for fields in field:
            try:     
                parsedField = ""
                name = fields.findall("name").pop().text
                tag = fields.attrib["tag"]
                if len(tag) > 3 or "X" in tag:
                    continue
                repeatable = fields.attrib["repeatable"]
                parsedField += "// " + name + "\n" + tag + self.fieldRepetitionSymbol(name, repeatable) + " | "
                for prop in fields:
                    inds = prop.findall("indicator")
                    if len(inds) > 0:
                        for i in inds:
                            iNum = i.attrib["num"]
                            iVals = []
                            for val in i.findall("values"):
                                for y in val:
                                    if y.attrib["code"] == "#":
                                        iVals.append("_")
                                    elif "-" in y.attrib["code"]:
                                        iVals.append(self.splitAreas(y.attrib["code"]))
                                    else:
                                        iVals.append(y.attrib["code"])
                                parsedField += "I" + iNum + "=" + "".join(iVals) + " | "
                    subfields = []
                    for x in prop.findall("subfield"):
                        sfCode = x.attrib["code"]
                        sfRep = x.attrib["repeatable"]
                        sfName = x.findall("name").pop().text
                        sf = (sfCode, sfRep, sfName)
                        subfields.append(sf)
                    
                    
                    if len(subfields) > 0:
                        for i, x in enumerate(subfields):
                            parsedField += "$" + subfields[i][0] + self.subfieldRepetitionSymbol(i, subfields, name) + " | "
                        if not "$5*" in parsedField:
                            parsedField += "$5* | "
                        if not "$9*" in parsedField:
                            parsedField += "$9* | "
                if not tag in self.parsedData:
                    self.parsedData[tag] = parsedField
            except:
                pass

    def parseControlField(self, cField):
        for fields in cField:         
            try:
                name = fields.findall("name").pop().text
                tag = fields.attrib["tag"]
                repeatable = fields.attrib["repeatable"]
                repetitionSymbol = ""
                if tag == "001" or tag == "003":
                    repetitionSymbol = "?"
                elif tag == "005" or tag == "008":
                    repetitionSymbol = "_"
                elif tag == "006" or tag == "007":
                    repetitionSymbol = "*"
                if not tag in self.parsedData:
                    self.parsedData[tag] = "// " + name + "\n" + tag + repetitionSymbol + " | I1= | I2= |"
            except:
                pass

    def fieldRepetitionSymbol(self, field, repeatable):
        if field == "245":
            return "_"
        elif repeatable == "Y":
            return "*"
        else:
            return "?"

    def subfieldRepetitionSymbol(self, subfield, subfields, fieldName):
        '''
        Osakenttä oletetaan pakolliseksi, jos:
            1) mahdollisia osakenttiä on vain yksi
            2) jos osakentän nimi on kentän nimen osajoukko
        '''
        repeatable = True if subfields[subfield][1] == "Y" else False
        mandatory = False
        sfName = subfields[subfield][2]
        if len(subfields) == 1 or sfName.lower() in fieldName.lower():
            mandatory = True
        if mandatory and repeatable:
            return "+"
        elif mandatory and not repeatable:
            return "_"
        elif not mandatory and not repeatable:
            return "?"
        else:
            return "*"

    def splitAreas(self, string):
        return "".join([str(x) for x in range(int(string.split("-")[0]), 1 + int(string.split("-")[1]))])

    def writeToFile(self, fileName):
        with open(fileName, 'w') as f:
            f.write("Format checking file\nGenerated: {0}\n\n".format(datetime.datetime.now()))
            for key in sorted(self.parsedData):
                f.write(self.parsedData[key])
                if not "I1" in self.parsedData[key]:
                    f.write("I1=_ | I2=_ |")
                f.write("\n\n")


if __name__ == "__main__":
    scraper = Scraper()
    parser = Parser(scraper.readData())
    parser.parseData()
    parser.writeToFile("ma_bibl.chk")