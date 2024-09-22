from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import hashlib
import hmac
import base64
import json
import re
from http import HTTPStatus
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request

VERB = "POST"

LOGIN_URL = '/v2/api/login'

CONTROL_URL= '/v2/api/control'

INVERTER_URL= '/v1/api/inverterList'

session = async_get_clientsession(hass)

log.error(f"hello world: solis_control Init")

def execute_request(url, data, headers) -> str:
    """execute request and handle errors"""
    post_data = data.encode("utf-8")
    request = Request(url, data=post_data, headers=headers)
    errorstring = ''
    try:
        with urlopen(request, timeout=30) as response:
            body = response.read()
            content = body.decode("utf-8")
            return content
    except HTTPError as error:
        errorstring = str(error.status) + ': ' + error.reason
    except URLError as error:
        errorstring = str(error.reason)
    except TimeoutError:
        errorstring = 'Request timed out'
    except socket.timeout:
        errorstring = 'Socket timed out'
    except Exception as ex:  # pylint: disable=broad-except
        errorstring = 'urlopen exception: ' + str(ex)
        traceback.print_exc()

    logging.error(url + " -> " + errorstring)
    time.sleep(60)  # retry after 1 minute
    return 'ERROR'


def digest(body: str) -> str:
    return base64.b64encode(hashlib.md5(body.encode('utf-8')).digest()).decode('utf-8')
    
def passwordEncode(password: str) -> str:
    md5Result = hashlib.md5(password.encode('utf-8')).hexdigest()
    return md5Result
    
def prepare_header_control(token, config: dict[str,str], body: str, canonicalized_resource: str) -> dict[str, str]:
    content_md5 = digest(body)
    content_type = "application/json;charset=UTF-8"
    
    now = datetime.now(timezone.utc)
    date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    encrypt_str = (VERB + "\n"
        + content_md5 + "\n"
        + content_type + "\n"
        + date + "\n"
        + canonicalized_resource
    )
    hmac_obj = hmac.new(
        config["secret"].encode('utf-8'),
        msg=encrypt_str.encode('utf-8'),
        digestmod=hashlib.sha1
    )
    sign = base64.b64encode(hmac_obj.digest())
    authorization = "API " + config["key_id"] + ":" + sign.decode('utf-8')
    
    contentLenght=str(len(body))
    
    header = {
        "Connection":"keep-alive",
        "token":token,
        "Date":date,
        "Content-MD5":content_md5,
        "Authorization":authorization,
        "Content-Type": content_type,
        "Content-Length": contentLenght,
        "Host":"www.soliscloud.com:13333"
    }
	
        #"User-Agent":"Apache-HttpClient/4.5.13(Java/11.0.17)"
	#"{ \"inverterSn\":\""+ "160F6221B300095" + "\", \"cid\":\"103\" }"



    return header


def prepare_header(config: dict[str,str], body: str, canonicalized_resource: str) -> dict[str, str]:
    content_md5 = digest(body)
    content_type = "application/json"
    
    now = datetime.now(timezone.utc)
    date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    encrypt_str = (VERB + "\n"
        + content_md5 + "\n"
        + content_type + "\n"
        + date + "\n"
        + canonicalized_resource
    )
    hmac_obj = hmac.new(
        config["secret"].encode('utf-8'),
        msg=encrypt_str.encode('utf-8'),
        digestmod=hashlib.sha1
    )
    sign = base64.b64encode(hmac_obj.digest())
    authorization = "API " + config["key_id"] + ":" + sign.decode('utf-8')
    
    header = {
        "Content-MD5":content_md5,
        "Content-Type":content_type,
        "Date":date,
        "Authorization":authorization
    }
    return header
    
def control_body(inverterId,inverterSn, chargeSettings) -> str:
    
    body = '{"inverterSn":"' + inverterSn  + '","inverterId":"'+inverterId+'", "cid":103, "value":"'
    
    for index, time in enumerate(chargeSettings):
        body = body +time['chargeCurrent']+","+time['dischargeCurrent']+","+time['chargeStartTime']+","+time['chargeEndTime']+","+time['dischargeStartTime']+","+time['dischargeEndTime']
        if (index !=2):
            body = body+","
    return body+'"}'

async def set_control_times(token, inverterId, inverterSn, config, times):
    
    log.warning("setting control times command")
    body = control_body(inverterId,inverterSn, times)
    

    log.warning(body)
    headers = prepare_header_control(token,config, body, CONTROL_URL)
    
 
    log.warning(headers)
    
    log.warning("https://www.soliscloud.com:13333"+CONTROL_URL)
    response = await session.post("https://www.soliscloud.com:13333" + CONTROL_URL, data = body, headers = headers)
    
    status = response.status
    log.error(response.status)

    log.warning("solis response:" + response.text())
    #log.warning("solis msg:" + response)

    
async def login(config):
    body = '{"userInfo":"'+config['username']+'","password":"'+ passwordEncode(config['password'])+'"}'
    header = prepare_header(config, body, LOGIN_URL)
    response = await session.post("https://www.soliscloud.com:13333"+LOGIN_URL, data = body, headers = header)
    status = response.status
    log.error(response.status)

    result = ""
    r = json.loads(re.sub(r'("(?:\\?.)*?")|,\s*([]}])', r'\1\2', response.text()))
    if status == HTTPStatus.OK:
        result = r
        log.error("login successful")
    else:
        log.warning(status)
        result = response.text()
    
    return result["csrfToken"]
    
async def getInverterList(config):
    
    body = '{"stationId":"'+ config['plantId']+'"}'

    log.error(body)
    
    header = prepare_header(config, body, INVERTER_URL)

    log.error(header)

    response = await session.post("https://www.soliscloud.com:13333"+INVERTER_URL, data = body, headers = header)

    log.error(response)

    log.error("to JSON")
    inverterList = response.json()

    log.error(inverterList)

    inverterId = ""
    
    for record in inverterList['data']['page']['records']:
        inverterId = record.get('id')
    return inverterId
   
@service   
async def solis_control(data=None,  **kwargs):
    log.info("Starting solis_control Service")

    config=data["config"]
    days=data["days"]

    log.info(config)
    log.info(days)

    inverterId= getInverterList(config)
    token = login(config)
    
    inverterSn=config['inverterSn']
    
    set_control_times(token, inverterId,inverterSn, config, days)
    
