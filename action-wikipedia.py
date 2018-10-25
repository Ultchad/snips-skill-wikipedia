#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import ConfigParser
from hermes_python.hermes import Hermes
import wikipedia


MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))


class SnipsConfigParser(ConfigParser.SafeConfigParser):
    def to_dict(self):
        return {section: {option_name: option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with open(configuration_file) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, ConfigParser.Error) as e:
        return dict()


LANG = 'fr'

ERROR_SENTENCES = {
    'en': {
        'DisambiguationError': u"Many pages was found on Wikipedia for your query: ",
        'PageError': u"Wikipedia no matched your query"
    },
    'fr': {
        'DisambiguationError': u"Plusieurs pages on été trouvé sur wikipédia pour votre recherche, la quel souaitez vous: ",
        'PageError': u"Aucune page n'a été trouvé sur wikipédia pour votre recherche"
    }
}


def searchWikipediaSummary(hermes, intentMessage):

    if intentMessage.slots.article_indicator:
        query = intentMessage.slots.article_indicator[0].slot_value.value.value
    else:
        print('article_indicator not found')
        hermes.publish_end_session(intentMessage.session_id, '')
        return None

    sentences = None
    if intentMessage.slots.sentences:
        sentences = intentMessage.slots.sentences[0].slot_value.value

    # Do the summary search

    session_continue = False
    wikipedia.set_lang(LANG)

    # print('Type query: {}, query: {}'.format(type(query), str(query)))
    # print('intentMessage.slots: {}'.format(intentMessage.slots))

    try:
        result = wikipedia.summary(str(query), auto_suggest=True, sentences=sentences)

    except wikipedia.exceptions.DisambiguationError, e:
        # Exception raised when a page resolves to a Disambiguation page.
        # The options property contains a list of titles of Wikipedia pages that the query may refer to.
        # may_refer = e.options

        # Removing duplicates in lists.
        # may_refer = list(set(may_refer))
        # session_continue = True
        result = '{}{}'.format(ERROR_SENTENCES[LANG]['DisambiguationError'], str(e.options))

    except wikipedia.exceptions.PageError:
        # Exception raised when no Wikipedia matched a query.
        result = ERROR_SENTENCES[LANG]['PageError']

    if session_continue:
        print('Session continue')
        hermes.publish_continue_session(intentMessage.session_id, result, ['searchWikipediaSummary'])
    else:
        hermes.publish_end_session(intentMessage.session_id, result)


if __name__ == "__main__":

    config = read_configuration_file("config.ini")

    if config.get("global") is not None:
        language = config["global"].get("locale", "fr_FR")

        if language.index('_') != -1:
            LANG = language[:language.index('_')].lower()

    with Hermes(MQTT_ADDR) as h:
        h.subscribe_intent("Tealque:searchWikipedia", searchWikipediaSummary).loop_forever()
