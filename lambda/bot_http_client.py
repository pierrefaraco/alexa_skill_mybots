import requests
import logging
from typing import Optional, Tuple, Union
class BotHttpClient:
    """HTTP client for interacting with RAG (Retrieval-Augmented Generation) system."""
    
    def __init__(self, virtual_alfred_url: str = 'https://virtualfred.com:444/api'):
        """
        Initialize the RAG HTTP client.
        
        Args:
            virtual_alfred_url (str): Base URL for the Virtual Alfred API
        """
        self.amazon_api_url = 'https://api.amazon.com'
        self.virtual_alfred_url = virtual_alfred_url
        self.token = ''
        self.logger = logging.getLogger(__name__)
    
    def get_amazon_client_id(self, handler_input) -> Optional[str]:
        """
        Extract Amazon client ID from handler input.
        
        Args:
            handler_input: Alexa handler input containing user access token
            
        Returns:
            Optional[str]: Amazon client ID if successful, None otherwise
        """
        try:
            amazon_token = handler_input.request_envelope.context.system.user.access_token
            if not amazon_token:
                self.logger.warning("No Amazon access token found")
                return None
                
            headers = {'Authorization': f'Bearer {amazon_token}'}
            user_info_url = f'{self.amazon_api_url}/user/profile'
            
            response = requests.get(user_info_url, headers=headers, timeout=60)
            response.raise_for_status()
            
            user_info = response.json()
            amazon_client_id = user_info.get('user_id')
            
            if not amazon_client_id:
                self.logger.error("user_id not found in Amazon user profile")
                return None
                
            return amazon_client_id
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching Amazon client ID: {e}")
            return None
        except (KeyError, AttributeError) as e:
            self.logger.error(f"Error parsing handler input: {e}")
            return None
    
    def login(self, handler_input) -> Tuple[Union[str, dict], int]:
        """
        Login using Amazon client ID.
        
        Args:
            handler_input: Alexa handler input
            
        Returns:
            Tuple[Union[str, dict], int]: (token/error_message, status_code)
        """
        amazon_client_id = self.get_amazon_client_id(handler_input)
        if not amazon_client_id:
            return "Failed to get Amazon client ID", 400
        
        payload = {"amazon_client_id": amazon_client_id}
        headers = {'Content-Type': 'application/json'}
        login_url = f'{self.virtual_alfred_url}/auth/amazon/login'
        
        try:
            response = requests.post(
                login_url, 
                headers=headers, 
                json=payload, 
                timeout=60
            )
            
            if response.status_code == 200:
                response_data = response.json()
                self.token = response_data.get('token', '')
                return self.token, 200
            else:
                error_message = response.json().get('message', 'Login failed')
                return error_message, response.status_code
                
        except requests.RequestException as e:
            self.logger.error(f"Login request failed: {e}")
            return f"Network error: {e}", 500
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing login response: {e}")
            return "Invalid response format", 500
    
    def post_query(self, question: str) -> Optional[str]:
        """
        Send a question to the RAG system.
        
        Args:
            question (str): Question to ask the RAG system
            
        Returns:
            Optional[str]: Response from Alfred, None if error
        """
        if not self.token:
            self.logger.error("No authentication token available")
            return None
            
        if not question.strip():
            self.logger.error("Empty question provided")
            return None
        
        payload = {'question': question}
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }
        chat_url = f'{self.virtual_alfred_url}/rag/chat'
        
        try:
            response = requests.post(
                chat_url, 
                headers=headers, 
                json=payload, 
                timeout=60
            )
            response.raise_for_status()
            
            response_data = response.json()
            return response_data.get('response')
            
        except requests.RequestException as e:
            self.logger.error(f"Error posting query: {e}")
            return None
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing query response: {e}")
            return None
    
    def trig_first_message(self) -> Optional[str]:
        """
        Trigger the first message from the RAG system.
        
        Returns:
            Optional[str]: First message response, None if error
        """
        if not self.token:
            self.logger.error("No authentication token available")
            return None
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }
        trigger_url = f'{self.virtual_alfred_url}/rag/trigfirstmessage?stream=False'
        
        try:
            response = requests.get(trigger_url, headers=headers, timeout=60)
            response.raise_for_status()
            
            response_data = response.json()
            return response_data.get('response')
            
        except requests.RequestException as e:
            self.logger.error(f"Error triggering first message: {e}")
            return None
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing first message response: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return bool(self.token)
    
    def logout(self):
        """Clear authentication token."""
        self.token = ''
        self.logger.info("Logged out successfully")
        