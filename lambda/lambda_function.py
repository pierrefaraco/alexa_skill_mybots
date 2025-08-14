
import logging

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.utils import  is_intent_name


from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.dispatch_components import AbstractResponseInterceptor
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

from bot_http_client import BotHttpClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


        
bot_http_client =  BotHttpClient()

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
           
        logger.info("=== can_handle LaunchRequestHandler ===")
        
        # Debug: afficher les informations sur la requête
        request = handler_input.request_envelope.request
        logger.info(f"Type de requête: {type(request).__name__}")
        logger.info(f"Request object_type: {getattr(request, 'object_type', 'Non défini')}")
        
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        logger.info('handle LaunchRequestHandler')
        # type: (HandlerInput) -> Response
        message, code = bot_http_client.login(handler_input)
        if code == 200:
            speak_output = bot_http_client.trig_first_message()
        else: 
            speak_output = message
        
        # Log pour debug de la session
        logger.info(f"LaunchRequestHandler - speak_output: {speak_output}")
        
        # Assure qu'Alexa attend la réponse complète de l'utilisateur
        reprompt_text = "Je vous écoute, posez-moi votre question."
        
        # Forcé à True pour test
        should_end_session = False
        
        logger.info(f"LaunchRequestHandler - should_end_session: {should_end_session}")
        logger.info(f"LaunchRequestHandler - reprompt_text: {reprompt_text}")
        
        response = (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .set_should_end_session(should_end_session)
                .response
        )
        
        logger.info(f"LaunchRequestHandler - response créée: {response}")
        return response
        
        #la requet est {'confirmation_status': 'NONE', 'name': 'MY_REQUEST', 'resolutions': None, 'slot_value': {'object_type': 'Simple', 'resolutions': None, 'value': 'ou est le sel'}, 'value': 'ou est le sel'} !

class CatchAllIntentHandler(AbstractRequestHandler):
    """Handler pour CatchAllIntent seulement"""
    def can_handle(self, handler_input):
        logger.info("=== can_handle CatchAllIntentHandler ===")
        request_type = ask_utils.get_request_type(handler_input)
        logger.info(f"request_type {request_type}")
        if request_type == 'IntentRequest':
            intent_name = ask_utils.get_intent_name(handler_input)
            logger.info(f"intent_name {intent_name}")
            return intent_name == "ChatIntent"

        return False

    def handle(self, handler_input):
        logger.info('handle CatchAllIntentHandler')
        slots = handler_input.request_envelope.request.intent.slots
        user_input = None

        if slots and "MY_QUERY" in slots and slots["MY_QUERY"].value:
            user_input = slots["MY_QUERY"].value

        if user_input:
            speak_output = bot_http_client.post_query(user_input)
        else:
            speak_output = "Je n'ai pas compris exactement, peux-tu reformuler ?"

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask("Que veux-tu ajouter ?")
            .response
        )


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler dédié pour AMAZON.FallbackIntent"""
    def can_handle(self, handler_input):
        logger.info("=== can_handle FallbackIntentHandler ===")
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        logger.info('handle FallbackIntentHandler')
        speak_output = "Je n'ai pas compris votre demande. Pouvez-vous reformuler votre question ?"
        
        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask("Que souhaitez-vous savoir ?")
            .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        logger.info('handle HelpIntentHandler')
        # type: (HandlerInput) -> Response
        speak_output = "Poser une question a Alfred, il vous répondra"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        logger.info('handle CancelOrStopIntentHandler')
        # type: (HandlerInput) -> Response
        speak_output = "A biento, n'hésitez pas à m'ivoquer!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.
        logger.info('handle class SessionEndedRequestHandler')

        return handler_input.response_builder.response




class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.info('handle class CatchAllExceptionHandler')
        logger.error(exception, exc_info=True)

        speak_output = f"Sorry, I had trouble doing what you asked. Please try again.{exception}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )
        
# This interceptor logs each request sent from Alexa to our endpoint.
class RequestLogger(AbstractRequestInterceptor):

    def process(self, handler_input):
        logger.debug("Alexa Request: {}".format(
            handler_input.request_envelope.request))

# This interceptor logs each response our endpoint sends back to Alexa.
class ResponseLogger(AbstractResponseInterceptor):

    def process(self, handler_input, response):
        logger.debug("Alexa Response: {}".format(response))

# This interceptor fetches the speech_output and reprompt messages from the response and pass them as
# session attributes to be used by the repeat intent handler later on.

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

# Ordre d'enregistrement important: handlers spécifiques d'abord, catch-all en dernier
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CatchAllIntentHandler())  # Handler principal qui capture le re
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())  # Handler dédié pour FallbackIntent

sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())



sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

lambda_handler = sb.lambda_handler()