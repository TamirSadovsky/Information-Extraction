# Submitted by: Liri Norkin (I.D. 208788448) and Tamir Sadovsky (I.D. 315316612)

import queue
import time
import sys
import urllib
import requests
import re
import traceback
import lxml.html
import rdflib
from urllib.parse import quote

# PART 1: Crawler & Extraction from infobox to ontology

start = time.time()
countries = []
visited = set()
g = rdflib.Graph()
# queue of urls: (Type, URL), Type = Country / President / Prime_Minister
url_queue = queue.Queue()

wiki_pre = "/wiki/"
prefix = "http://en.wikipedia.org"
ontology_prefix = "http://example.org/"
url_source = "https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)"

data_labels = ["president", "prime_minister", "population", "area", "government", "capital", "Country", "where_born", "when_born"]
g = rdflib.Graph()
count_based_on = 0

def extract_country_from_url(url):
    # This function gets a wikipedia link of a country and returns the name of the country
    return url.split("/")[-1].replace("_", " ")

def data_spaces_to_underlines(question):
    # This function replaces spaces of given string with underlines
    return question.replace(" ", "_")

def data_hyphens_to_underlines(question):
    # This function replaces hyphens of given string with underlines
    return question.replace("-", "_")
def remove_hyphens(question):
    # This function removes hyphens of given string
    return question.replace("-", "")
def remove_underlines(question):
    # This function removes underlines of given string
    return question.replace("_", "")

def add_to_ontology(entity, description, result):
    """
    This function gets a triple of:
    @param entity = country / prime minister / president
    @param description = from data_labels (list)
    @param result data = population, capital, etc

    Result: adds the data to the ontology
    """

    if len(entity) > 0 and len(description) > 0 and len(result) > 0:
        entity = f"{ontology_prefix}{entity}"
        description = f"{ontology_prefix}{description}"
        result = f"{ontology_prefix}{data_spaces_to_underlines(result)}"
        g.add((rdflib.URIRef(entity), rdflib.URIRef(description), rdflib.URIRef(result)))


def from_source_url_to_queue():
    """
    This function initialize the url_queue.
    It enters a tuple of: <"Country"> , <Country URL> to queue.
    special array handles special cases of 3 countries that have symbols in their wikipedia link page.
    In addition it initialize countries list from the given page in the task.
    """
    r = requests.get(url_source)
    doc = lxml.html.fromstring(r.content)
    inte = 0
    for t in doc.xpath('//*[@id="mw-content-text"]/div[1]/table/tbody//tr/td[1]//a[@title]/@href'):
        if t not in visited:
            inte = inte + 1
            visited.add(t)
            if "%" in t:
                t = urllib.parse.unquote(t)
                wiki = prefix
                wiki = data_spaces_to_underlines(wiki)
                url_queue.put((data_labels[6], f"{wiki}{t}"))
            else:
                if t != "/wiki/French_Fifth_Republic" and t != "/wiki/Realm_of_New_Zealand" and t != "/wiki/Danish_Realm" and t != "/wiki/Kingdom_of_the_Netherlands":
                    url_queue.put((data_labels[6], f"{prefix}{t}"))
            if t[6:len(t)] != "o" and t[6:len(t)] != "n" and t[6:len(t)] != "French_Fifth_Republic" and t[6:len(t)] != "Realm_of_New_Zealand" and t[6:len(t)] != "Danish_Realm" and t[6:len(t)] != "Kingdom_of_the_Netherlands":
                countries.append(t[6:len(t)])
                countries.append(remove_underlines(t[6:len(t)]))


def add_population(country, doc):
    """
    This function extract the population size of country with XPATH query.
    @param country = given country
    @param doc = country page

    Result: adds the data to the ontology
    """
    population = doc.xpath('//table[contains(@class,"infobox")]/tbody//tr[contains(.//text(),"Population")]/following-sibling::tr/td//text()')
    if country == "Russia":
        population = doc.xpath('//table[contains(@class,"infobox")]/tbody//tr[contains(.//text(),"Population")]/following-sibling::tr/td/div/ul/li/text()')
    elif country == "Dominican_Republic":
        population = doc.xpath('//*[@id="mw-content-text"]/div[1]/table[1]/tbody/tr[37]/td/span/text()')
    elif country == "Channel_Islands":
        population = doc.xpath('//*[@id="mw-content-text"]/div[1]/table[1]/tbody/tr[21]/td/text()[1]')
    if population:
        population = population[0].split("(")[0]
        population = str(population).replace(".", ",").replace(" ", "")
        add_to_ontology(country, data_labels[2], str(population))


def add_government(country, doc):
    """"
    This function extract the form government of country with XPATH query.
    @param country = given country
    @param doc = country page

    Result: adds the data to the ontology
    """
    government = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Government"]//a/@href')
    government = government[1:]
    val_to_remove = []
    for i in range(len(government)):
        government[i] = government[i][6:]
        government[i] = urllib.parse.unquote(government[i], encoding='utf-8', errors='ignore')
        if ("'" in government[i]):
            government[i] = str(government[i]).replace("'", "")
        if ('[' in government[i] or '#' in government[i] or 'note-' in government[i]):
            val_to_remove.append(government[i])
    for val in val_to_remove:
        government.remove(val)
    government = sorted(government, key=str.lower)
    if len(government) > 0:
        for gov in government:
            add_to_ontology(country, data_labels[4], str(gov))


def add_birth_location(person, url):
    """"
    This function extract the birth location of prime minister / president with XPATH query.
    @param person = prime minister / president
    @param url = prime minister / president wikipedia page

    Result: adds the data to the ontology
    """
    r = requests.get(url)
    doc = lxml.html.fromstring(r.content)
    location_list = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Born"]/td//text()')
    list_from_title = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Born"]/td//@title')

    location = ""
    for loc in location_list:
        check = data_spaces_to_underlines(loc)
        if check in countries:
            location = loc
            break
        else:
            # replace chars that can be in string with spaces
            check = loc.replace(" ", "_").replace(",", "").replace(".", "").replace(")", "").replace("(", "")
            if check in countries:
                location = check
                break
    if location == "" and location_list:
        for country in countries:
            for location_check in location_list:
                location_check = location_check.replace(" ", "_")
                if country in location_check:
                    location = country
    if location == "" and list_from_title:
        for country in countries:
            for title in list_from_title:
                title = title.replace(" ", "_")
                if country in title:
                    location = country
                    break
    # string special chars were regular in this case of infobox, so added manually
    if person == "Jorge_Bom_Jesus":
        location = "São_Tomé_and_Príncipe"
    if location:
        location = data_spaces_to_underlines(location)
        add_to_ontology(person, data_labels[7], location)


def add_birthday(person, url):
    """"
    This function extract the birthday of prime minister / president with XPATH query.
    @param person = prime minister / president
    @param url = prime minister / president wikipedia page

    Result: adds the data to the ontology
    """
    r = requests.get(url)
    doc = lxml.html.fromstring(r.content)
    birthday = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Born"]//span[@class="bday"]//text()')
    if birthday:
        birthday = data_hyphens_to_underlines(birthday[0])
        add_to_ontology(person, data_labels[8], birthday)


def add_area(country, doc):
    """"
    This function extract the area size of country with XPATH query.
    @param country = given country
    @param doc = country page

    Result: adds the data to the ontology
    """
    area = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr//td[text()[contains(.,"km")]]//text()')
    if len(area) > 0:
        area = str(area[0].split()[0])
        add_to_ontology(country, data_labels[3], area)


def add_capital(country, doc):
    """"
    This function extract the capital city of country with XPATH query.
    @param country = given country
    @param doc = country page

    Result: adds the data to the ontology
    """
    capital = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Capital"]//@title')
    url_capital = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Capital"]/td//a/@href')
    if url_capital:
        capital = url_capital[0]
        if country == "Switzerland":
            capital = url_capital[1]
        capital = extract_country_from_url(capital)
        capital = urllib.parse.unquote(capital, encoding='utf-8', errors='ignore')
        capital = data_spaces_to_underlines(capital)

        if capital != "#cite_note-2":
            add_to_ontology(country, data_labels[5], capital)
    elif capital:
        capital = data_spaces_to_underlines(capital[0])
        add_to_ontology(country, data_labels[5], capital)
    else:
        if country == "Channel_Islands":
            capital = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Capital and largest settlement"]//@title')
            capital = data_spaces_to_underlines(capital[0])
            capital = urllib.parse.quote(capital)
            add_to_ontology(country, data_labels[5], capital)


def add_president_or_prime_minister(country, person, url_person, role):
    """"
    This function extract the form government of country with XPATH query.
    @param country = given country
    @param person = prime minister / president name
    @param url_person = prime minister / president wikipedia page
    @param role = role of entity from data_labels (prime minister / president)

    Result: adds the data to the ontology
    """
    if url_person:
        person = url_person[0]
        person = extract_country_from_url(person)
        person = urllib.parse.unquote(person, encoding='utf-8', errors='ignore')
        person = person.replace('"', "@")

        person = data_spaces_to_underlines(person)
        url_person = url_person[0]
        url_person = f"{prefix}{url_person}"
        add_birthday(person, url_person)
        add_birth_location(person, url_person)
        add_to_ontology(country, role, person)
        add_to_ontology(person, role, country)

    else:
        if person:
            person = person[0]
            person = data_spaces_to_underlines(person)
            url_person = f"{prefix}{url_person}"
            add_birthday(person, url_person)
            add_birth_location(person, url_person)
            add_to_ontology(country, role, person)
            add_to_ontology(person, role, country)


def get_from_url(job):
    """"
    Main function.
    The function manages every country url it gets from the initialize_crawl function.
    The function sends each request to a small function which extracts all the data
    it needs from country like: area,capital,population etc.

    @param job = tuple of : <"Country"> , <Country URL>.

    Result: manages the build of the ontology
    """
    url = job[1]
    # print(url)
    country = data_spaces_to_underlines(extract_country_from_url(url))
    # print(country)
    r = requests.get(url)
    doc = lxml.html.fromstring(r.content)

    president = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="President"]/td//text()')
    url_president = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="President"]/td//a/@href')
    prime_minister = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Prime Minister"]/td//text()')
    url_prime_minister = doc.xpath('//table[contains(@class, "infobox")]/tbody/tr[th//text()="Prime Minister"]/td//a/@href')

    add_capital(country, doc)
    add_area(country, doc)
    add_government(country, doc)
    add_population(country, doc)

    # handle special cases
    if president:
        if president[0] == '\xa0':
            president = ""
    if prime_minister:
        if prime_minister[0].find("TBA") != -1:
            prime_minister = ""
    add_president_or_prime_minister(country, president, url_president, data_labels[0])
    add_president_or_prime_minister(country, prime_minister, url_prime_minister, data_labels[1])


def initialize_crawl():
    """
    This function manages the queue of country links.
    The function sends country link to get_from_url function until the queue is empty.

    Result: It creates the ontology
    """
    # queue of urls
    from_source_url_to_queue()
    while not url_queue.empty():
        job = url_queue.get()
        get_from_url(job)
    g.serialize("ontology.nt", encoding='utf-8', format="nt")

# *** Part 2 - Answer Questions ***


def find_part_for_query(question):
    length_q = len(question)
    question = data_spaces_to_underlines(question)
    part_for_query = ""
    part_for_query2 = ""
    relation = ""
    switch_case = ["1", "area", "are_also", "find_entity", "when_born", "where_born", "how_many_pres", "list_all", "8", "ERROR"]
    president = False
    prime_minister = False
    case = 0
    # question starting with Who
    if question.find("Who") != -1:

        # Who is the president of <country>?
        if question.find("president") != -1:
            part_for_query = question[24:length_q - 1]
            relation = "president"
            case = switch_case[0]

        # Who is the prime minister of <country>?
        elif question.find("prime") != -1:
            part_for_query = question[29:length_q - 1]
            relation = "prime_minister"
            case = switch_case[0]

        # Who is <entity>?
        else:
            part_for_query = question[7:length_q - 1]
            case = switch_case[3]

    # question starting with What
    if question.find("What") != -1:
        case = switch_case[0]

        # What is the area of <country>?
        if question.find("area") != -1:
            part_for_query = question[20:length_q - 1]
            relation = "area"
            case = switch_case[1]
        # What is the population of <country>?
        if question.find("population") != -1:
            part_for_query = question[26:length_q - 1]
            relation = "population"

        # What is the capital of <country>?
        if question.find("capital") != -1:
            part_for_query = question[23:length_q - 1]
            relation = "capital"

        # What is the form of government in <country>?
        if question.find("government") != -1:
            part_for_query = question[34:length_q - 1]
            relation = "government"

    # question starting with When
    if question.find("When") != -1:
        relation = "when_born"
        # When was the president of <country> born?
        if question.find("president") != -1:
            part_for_query = question[26:length_q - 6]
            case = switch_case[4]
            president = True

        # When was the prime minister of <country> born?
        elif question.find("prime") != -1:
            part_for_query = question[31:length_q - 6]
            case = switch_case[4]
            prime_minister = True

    # question starting with where
    if question.find("Where") != -1:
        relation = "where_born"
        # Where was the president of <country> born?
        if question.find("president") != -1:
            part_for_query = question[27:length_q - 6]
            case = switch_case[5]
            president = True

        # Where was the prime minister of <country> born?
        elif question.find("prime") != -1:
            part_for_query = question[32:length_q - 6]
            case = switch_case[5]
            prime_minister = True

    # How many presidents were born in <country>?
    if question.find("were_born_in") != -1:
        part_for_query = question[33:length_q-1]
        case = switch_case[6]
        relation = "where_born"

    # List all countries whose capital name contains the string <str>
    if question.find("List_all") != -1:
        part_for_query = question[58:length_q]
        case = switch_case[7]
        relation = "capital"

    # How many <government_form1> are also <government_form2>?
    if question.find("are_also") != -1:
        # government form1
        are_also = question.find("are_also")
        part_for_query = question[9:are_also-1]
        # government form2
        part_for_query2 = question[are_also+9:length_q - 1]
        case = switch_case[2]

    # Does prime minister born in <country>?
    if question.find("Does") != -1:
        in_ = question.find("in")
        part_for_query = question[in_+3:length_q - 1]
        case = switch_case[8]
        relation = "where_born"
        born = question.find("born")
        part_for_query2 = question[5:born-1]

    if case == switch_case[0]  or case == switch_case[1]:
        return "select * where {<http://example.org/" + part_for_query + "> <http://example.org/" + relation + "> ?a.}" , case

    # <gov1> <are also> <gov 2>
    elif case == switch_case[2]:
        return "select DISTINCT ?a where {?a <http://example.org/government> <http://example.org/" + part_for_query + ">. ?a <http://example.org/government> <http://example.org/" + part_for_query2 + ">.}", case

    #Who is <entity>?
    elif case == switch_case[3]:
        return "select ?a ?b where {?a ?b  <http://example.org/" + part_for_query + ">.}" , case

    #When/Where was the president/prime minister of <country> born?
    elif case == switch_case[4] or case == switch_case[5]:
        if president:
            return "select DISTINCT ?a where {?x <http://example.org/president> <http://example.org/" + part_for_query + ">. ?x <http://example.org/" + relation + "> ?a.}", case
        if prime_minister:
            return "select DISTINCT ?a where {?x <http://example.org/prime_minister> <http://example.org/" + part_for_query + ">. ?x <http://example.org/" + relation + "> ?a.}", case

    #How many presidents were born in <country>?
    elif case == switch_case[6]:
        #print(part_for_query)
        return "select ?a where {?a <http://example.org/president> ?x. ?a <http://example.org/" + relation + "> <http://example.org/" + part_for_query + ">. }", case

    #List all countries whose capital name contains the string <str>
    elif case == switch_case[7]:
        return "select ?a where {?a <http://example.org/" + relation + "> ?b. filter(contains(lcase(str(?b)),'"+part_for_query+"'))}", case

    # extra question -
    # Does <prime minister> born in <country>?
    elif case == switch_case[8]:
        real_country = "select ?a where {<http://example.org/" + part_for_query2 + "> <http://example.org/" + relation + "> ?a.}"
        case = part_for_query + case
        return real_country, case

    # If the input question doesn't any pattern:
    case = switch_case[-1]
    return "ERROR", case


def question(input_question):
    input_question = data_spaces_to_underlines(input_question)
    query, case = find_part_for_query(input_question)
    query = query.replace("<http://example.org/Philip_Brave_Davis>", "<http://example.org/Philip_@Brave@_Davis>")
    if case == "ERROR":
        return("ERROR")
    g = rdflib.Graph()
    g.parse("ontology.nt", format="nt")
    query_result = g.query(query)

    res_string = ""
    if case == 'are_also' or case == 'how_many_pres':
        print(len(list(query_result)))
        return len(list(query_result))
    elif case == "1" or case == "area" or case == "where_born" or case=="list_all" or case[-1] == "8":
        for i in range (len(list(query_result))):
            row = list(query_result)[i]
            entity_with_uri = str(row[0])
            entity_with_uri = entity_with_uri.split("/")
            entity_without_uri = entity_with_uri[-1]
            #strip excessive spaces.
            entity_without_uri = entity_without_uri.replace("_", " ")
            entity_without_uri = entity_without_uri.strip()
            entity_without_uri = entity_without_uri.replace(" ", "_").replace("@", '"')
            res_string += entity_without_uri + " "
        names = res_string.split()
        names.sort()
        res_string = ""
        for j in range (len(list(names))): #build string of names separated by ', '
            res_string += names[j]+", "
        res_string = res_string[0:len(res_string)-2] #remove the last ', ' in the string
        res_string = res_string.replace("_", " ")
        if case == "area":
            res_string += " km squared"
        if res_string == "579,330or392,040": # Execption in Maldives
            res_string = "579,330 or 392,040"
    elif case == "find_entity":
        res_string = ""
        all_jobs = ["" for i in range(len(query_result))]
        for i in range(len(query_result)):
            query_result_i = str(list(query_result)[i]).split(",")
            query_result_i = [x.replace("(", "").replace(")", "") for x in query_result_i]
            query_result_i = query_result_i[::-1]
            entity_with_uri = [x.split("/") for x in query_result_i]
            entity_without_uri = entity_with_uri[0][-1] + entity_with_uri[1][-1]
            entity_without_uri = entity_without_uri.replace("_", " ").replace("'", "")
            if entity_without_uri[:9] == "president":
                entity_without_uri = "President of " + entity_without_uri[9:]
            elif entity_without_uri[:14] == "prime minister":
                entity_without_uri = "Prime Minister of " + entity_without_uri[14:]

            all_jobs[i] = entity_without_uri
        all_jobs = sorted(all_jobs)
        for i in range(len(query_result)):
            res_string += all_jobs[i]
            if len(query_result) > 1 and i < len(query_result) - 1:
                res_string += ", "

    elif case == "when_born":
        for i in range(len(list(query_result))):
            row = list(query_result)[i]
            entity_with_uri = str(row[0])
            entity_with_uri = entity_with_uri.split("/")
            entity_without_uri = entity_with_uri[-1]
            entity_without_uri = entity_without_uri.replace("_", "-")
            res_string = entity_without_uri

    if case[-1] == "8":
        res_string = case[:-1] == res_string.replace(" ", "_")

    print(res_string)
    return res_string


if __name__ == '__main__':
    mood = sys.argv[1]
    if mood == "question":
        question(sys.argv[2])
    elif mood == "create":
        initialize_crawl()
