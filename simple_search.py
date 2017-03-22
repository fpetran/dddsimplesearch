#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Script for performing a simplified search on Annis within the REM project

Ruhr-Universität Bochum
Sprachwissenschaftliches Institut

Script by Janis Pagel
based on a script by Tom Ruette, HU Berlin
'''

# import needed modules
import urllib2, re, urllib, codecs
import cgi
#import cgitb
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


ANNOTATION_RAUM="meta::language-region"
ANNOTATION_ZEIT="meta::time"
ANNOTATION_TEXT="meta::topic"


def getREMCorpora():
    # function for reading in all available xml-filenames of REM

    xml = urllib.urlopen('http://smokehead.linguistics.rub.de/annis-service/annis/query/corpora').read().decode("utf-8")
    regex = re.compile("<name>(.+?)</name>")

    return regex.findall(xml)


def getREMAnnotations(corpora):
    # function for reading in all attributes

    annodict = {}

    for corpus in corpora:

        url = str("http://smokehead.linguistics.rub.de/annis-service/annis/query/corpora/" + corpus + "/annotations") #?fetchvalues=true&onlymostfrequentvalues=false")

        xml = urllib.urlopen(url).read().decode("utf-8")

        regexAttr = re.compile("<annisAttribute>(.+?)</annisAttribute>", re.DOTALL)
        regexAttrName = re.compile("<name>(.+?)</name>")
        regexValues = re.compile("<value>(.+?)</value>")
        attributes = regexAttr.findall(xml)

        for attribute in attributes:

            name = regexAttrName.findall(attribute)
            if len(name) == 0:
                continue
            name = name[0]
            values = regexValues.findall(attribute)

            try:

                annodict[name].extend(values)
                annodict[name] = list(set(annodict[name]))

            except KeyError:

                annodict[name] = list(set(values))


    return annodict

def aql(ps, strict):
    # function for creating a valid aql search-string for annis

    numbers = ""
    statements = ""

    if len(ps) > 1:

        j = 1
        i = 1

        for p in ps:

            statements = statements + p + " &\n"

        while i <= len(ps) and j < ((len(ps) * 2) - 1):

            if j%2 == 1:

                numbers = numbers + "#" + str(i)
                i += 1

            if j%2 == 0:

                if strict == True:

                    numbers = numbers + ". #" + str(i) + " &\n"

                if strict == False:

                    numbers = numbers + " .1,3 #" + str(i) + " &\n"

            j += 1

    if len(ps) == 1:

        statements = ps[0]

    return unicode(statements + numbers).strip("&\n").encode("utf-8")

def resolveDiacritics(word):
    # function for resolve all Diacritics which occur within the REM annotations

    word = word.encode("utf-8")
    
    diacritics = {ur"i": ur"[iî\u0131\u0304\u0306\u0131\u0304\u0131\u0306]",
                  ur"u": ur"[uûu\u0304\u0306u\u0304u\u0306ü]",
                  ur"o": ur"[oôo\u0304\u0306o\u0304o\u0306]",
                  ur"z": ur"[z\u01B7]",
                  ur"s": ur"[sß\u017F]",
                  ur"d": ur"[d\u0110\u0111\u00DE\u00FE]",
                  ur"e": ur"[eêe\u0304\u0306e\u0304e\u0306\u025B\u03B5ē\u00eb\u00cb\u00e8\u00c8]",
                  ur"a": ur"[aâ]",
                  ur"n": ur"[n\u00f1\u00d1]"
    }

    if re.search("\[(.*)\]", word):

        return word

    else:

        for letter in diacritics.keys():

            word = word.replace(letter, diacritics[letter])

    return word

# a function to pass to re.sub that replaces A -> Aa
def upcase_to_regex(matchobj):
    return "[" + matchobj.group(0) + matchobj.group(0).lower() + "]"

# make a string into a case-insensitive regex
# e.g. Poesie -> [Pp]oesie
def make_i_regex(s):
    my_s = re.sub(r'[A-Z]', upcase_to_regex, s)
    return my_s

def parseQuery(d):

    annolevel = d["scope"][0]
    words = make_i_regex(d["query"][0])
    if d["search_method"][0] == "begins_with_word":
        words = words + ".*"
    elif d["search_method"][0] == "ends_with_word":
        words = ".*" + words
    return aql([annolevel + "=/" + words + "/"], False)

def regexescape(s):
    s = s.replace("|", "\|")
    s = s.replace("(", "\(")
    s = s.replace(")", "\)")
    s = s.replace(".", "\.")
    return s

def parseZeit(d):
    out = []
    try:
        eras = d["dating"]
        for era in eras:
            out.append(".*" + era + ".*")
        return unicode(ANNOTATION_ZEIT + "=/(" + "|".join(out) + ")/").encode("utf-8")
    except KeyError:
        return ""

def parseRaum(d):
    out = []
    try:
        locs = d["location"]
        for loc in locs:
            out.append(".*" + make_i_regex(loc) + ".*")
        return unicode(ANNOTATION_RAUM + "=/(" + "|".join(out) + ")/").encode("utf-8")
    except KeyError:
        return ""

def parseText(d):
    out = []
    try:
        regs = d["textfield"]
        for reg in regs:
            out.append(".*" + make_i_regex(reg) + ".*")
        return unicode(ANNOTATION_TEXT + "=/(" + "|".join(out) + ")/").encode("utf-8")
    except KeyError:
        return ""

def createAQL(query, zeit, raum, text):
    baseurl = "http://smokehead.linguistics.rub.de/annis3/REM/#"
    aqlurl = ""
    if query:
        aqlurl = query.strip()
    if text:
        aqlurl = str(aqlurl).strip() + " & " + str(text).strip()
    if zeit:
        aqlurl = str(aqlurl).strip() + " & " + str(zeit).strip()
    if raum:
        aqlurl = str(aqlurl).strip() + " & " + str(raum).strip()
    aqlstr = aqlurl.strip()
    aqlurl = "_q=" + aqlurl.encode("base64")
    corpora = getREMCorpora()
    scope = "&_c=" + unicode(",".join(corpora)).encode("base64").strip() + "&cl=7&cr=7&s=0&l=30&_seg=dG9rX2RpcGw"
    return aqlstr, unicode(baseurl.strip() + aqlurl.strip() + scope.strip()).replace('\n', '')

def cgiFieldStorageToDict(fieldStorage):
    params = {}
    for key in fieldStorage.keys():
        params[key] = fieldStorage.getlist(key)
    return params

def form2aql(form, adict):
    d = cgiFieldStorageToDict(form)
    query = parseQuery(d)
    zeit = parseZeit(d)
    raum = parseRaum(d)
    text = parseText(d)
    return createAQL(query, zeit, raum, text)

corpora = getREMCorpora()
annos = getREMAnnotations(corpora)
#cgib.enable(display=1)
form = cgi.FieldStorage()

aqlstr, url = form2aql(form, annos)


print "Content-Type: text/html\n"
print '<!DOCTYPE html>'
print '<html>'
print '<head><title>Performing simplified search</title>'
print '<meta HTTP-EQUIV="content-type" content="text/html; charset=utf-8">'
print '<meta HTTP-EQUIV="REFRESH" content="0; url=' + url + '"></head>'
print '<body>'
print '<p>you will be redirected in 0 seconds</p>'
print '<p>'
print cgiFieldStorageToDict(form)
print '</p>'
print '<a href="' + url + '">perform the search in Annis</a>'
print '<pre>AQL query: ' + aqlstr + '</pre>'
print '<pre>url: ' + url + '</pre>'
print '</body>'
print '</html>'

