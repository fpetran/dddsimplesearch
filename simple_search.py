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


def getREMCorpora():
    # function for reading in all available xml-filenames of REM

    xml = urllib.urlopen('http://smokehead.linguistics.rub.de/annis-service/annis/query/corpora').read().decode("utf-8")
    regex = re.compile("<name>(.+?)</name>")

    return regex.findall(xml)


def getREMAnnotations(corpora):
    # function for reading in all attributes

    annodict = {}

    for corpus in corpora:

        url = str("http://smokehead.linguistics.rub.de/annis-service/annis/query/corpora/" + corpus + "/annotations?fetchvalues=true&onlymostfrequentvalues=false")

        xml = urllib.urlopen(url).read().decode("utf-8")
        
        regexAttr = re.compile("<annisAttribute>(.+?)</annisAttribute>", re.DOTALL)
        regexAttrName = re.compile("<name>(.+?)</name>")
        regexValues = re.compile("<value>(.+?)</value>")
        attributes = regexAttr.findall(xml)

        for attribute in attributes:

            name = regexAttrName.findall(attribute)[0]
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

def parseQuery(d, a):

    annolevel = d["scope"][0]
    strict = False
    try:
        if d["query"][0].startswith("\"") and d["query"][0].endswith("\""):
            strict = True
        words = d["query"][0].split()
        parameters = []
    except KeyError:
        words = [""]
        parameters = []
    for word in words:
        search = ""
        worddiacritics = resolveDiacritics(word.strip("\""))
        regex = re.compile(r"\b" + worddiacritics + r"\b", re.UNICODE | re.IGNORECASE)
        #regex = re.compile(r"\b" + word + r"\b", re.UNICODE | re.IGNORECASE)
        searchlist = []
        try:
            for annoattr in a[annolevel]:
                for hit in regex.findall(annoattr):
                    if d["search_method"][0] == "hole_string":
                        hit = regexescape(hit)
                    elif d["search_method"][0] == "begins_with_word":
                        hit = regexescape(hit) + ".*"
                    elif d["search_method"][0] == "ends_with_word":
                        hit = ".*" + regexescape(hit)
                    if hit not in searchlist:
                        searchlist.append(hit)
        except KeyError:
            continue

        search = annolevel[11:] + "=/(" + "|".join(searchlist) + ")/"

        if search:
            parameters.append(search)

    return aql(parameters, strict)

def regexescape(s):
    s = s.replace("|", "\|")
    s = s.replace("(", "\(")
    s = s.replace(")", "\)")
    s = s.replace(".", "\.")
    return s

def parseZeit(d, a):
    out = []
    try:
        eras = d["dating"]
        poseras = a["default_ns:entry_dating_val"]
        for era in eras:
            regex_era = re.compile(era, re.IGNORECASE)
            for posera in poseras:
                if regex_era.search(posera):
                    if posera not in out:
                        out.append(posera.replace('?', '\?'))
        query = unicode("meta::entry_dating_val=/(" + "|".join(out) + ")/").encode("utf-8")
        return query
    except KeyError:
        return ""

def parseRaum(d, a):
    out = []
    try:
        locs = d["location"]
        poslocs = a["default_ns:entry_dialect_val"]
        for loc in locs:
            regex_loc = re.compile(loc, re.IGNORECASE)
            for posloc in poslocs:
                if regex_loc.search(posloc):
                    if posloc not in out:
                        out.append(posloc.replace('?', '\?'))
        query = unicode("meta::entry_dialect_val=/(" + "|".join(out) + ")/").encode("utf-8")
        return query
    except KeyError:
        return ""

def parseText(d, a):
    out = []
    try:
        regs = d["textfield"]
        posregs = a["default_ns:general_text_field_val"]
        for reg in regs:
            regex_reg = re.compile(reg, re.IGNORECASE)
            for posreg in posregs:
                if regex_reg.search(posreg):
                    if posreg not in out:
                        out.append(posreg.replace('?', '\?'))
        query = unicode("meta::general_text_field_val=/(" + "|".join(out) + ")/").encode("utf-8")
        return query
    except KeyError:
        return ""

def createAQL(query, zeit, raum, text):
    baseurl = "http://smokehead.linguistics.rub.de/annis3#"
    aqlurl = ""
    if query:
        aqlurl = query.strip()
    if text:
        aqlurl = str(aqlurl) + " & " + str(text.strip())
    if zeit:
        aqlurl = str(aqlurl) + " & " + str(zeit.strip())
    if raum:
        aqlurl = str(aqlurl) + " & " + str(raum.strip())
    aqlurl = "_q=" + aqlurl.encode("base64")
    aqlstr = query + text + zeit + raum
    corpora = getREMCorpora()
    scope = "&_c=" + unicode(",".join(corpora)).encode("base64") + "&cl=7&cr=7&s=0&l=30"
    return aqlstr, unicode(baseurl.strip() + aqlurl + scope.strip())

def cgiFieldStorageToDict(fieldStorage):
    params = {}
    for key in fieldStorage.keys():
        params[key] = fieldStorage.getlist(key)
    return params

def form2aql(form, adict):
    d = cgiFieldStorageToDict(form)
    #d = {"query": ["got"], "textfield": ["religion"], "scope": ["default_ns:tok_mod"], "dating": ["13"], "search_method": ["hole_string"]}
    query = parseQuery(d, adict)
    zeit = parseZeit(d, adict)
    raum = parseRaum(d, adict)
    text = parseText(d, adict)
    return createAQL(query, zeit, raum, text)

corpora = getREMCorpora()
annos = getREMAnnotations(corpora)
#cgitb.enable(display=1)
form = cgi.FieldStorage()

aqlstr, url = form2aql(form, annos)


print "Content-Type: text/html\n"
print '<!DOCTYPE html>'
print '<html>'
print '<head><title>Performing simplified search</title><meta HTTP-EQUIV="REFRESH" content="0; url=' + url + '"></head>'
print '<body>'
print '<p>you will be redirected in 0 seconds</p>'
print cgiFieldStorageToDict(form)
print '<a href="' + url + '">perform the search in Annis</a>'
print '<pre>AQL query: ' + aqlstr + '</pre>'
print '<pre>url: ' + url + '</pre>'
print '</body>'
print '</html>'

