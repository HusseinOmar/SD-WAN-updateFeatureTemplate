#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2023 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""


__author__ = "Hussein Omar, CSS - ANZ"
__email__ = "husseino@cisco.com"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2021 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

'''
This Module is written to help automate updating Feature Templates.
The following abbreviations will be used

fTem: Feature Template
dTem: Device Template
'''


# --> Imports
import json
from vAPI import main as vapi

# -> Global Variables

session = vapi()

# --> Core Functions


def getFTemIdByName(fTemName: str) -> str:
    '''
    Get Feature Template ID by supplying template Name
    '''
    allFTems = session.getDataResponse(
        '/dataservice/template/feature')
    for template in allFTems:
        if template['templateName'] == fTemName:
            return template['templateId']
    else:
        print(f"Template name {fTemName} NOT FOUND!")
        exit()


def getDTemByFTemId(fTemID: str) -> list:
    '''
    Return list of device templates using supplied feature template ID.
    returns
    '''
    return session.getDataResponse(f'/dataservice/template/feature/devicetemplates/{fTemID}')


def openUpdateFile(fileName: str) -> dict:
    '''
    Opens feature template update stored in json file format
    '''
    with open(fileName, 'r') as file:
        return json.load(file)


def step1pushUpdate(fTemId: str, update: dict) -> list:
    '''
    Step01: Push Feature Template Update, returns all device templates affected my this update
    '''
    print('=> Step1 Pushing Update')
    try:
        response = session.putRequest(
            f'/dataservice/template/feature/{fTemId}', json.dumps(update))
        return response.json()['masterTemplatesAffected']
    except:
        print(response.text)
        exit()


def step2payload(dTemAffected: str) -> dict:
    '''
    Step2: Define the list of devices recieving the config update
    Return the dictionary payload that will be used in the next API call
    '''
    print('=> Prepare device list')
    payload = {
        "templateId": dTemAffected,
        "deviceIds": [],
        "isEdited": True,
        "isMasterEdited": False
    }
    response = session.getDataResponse(
        f"/dataservice/template/device/config/attached/{dTemAffected}")
    for device in response:
        try:
            payload['deviceIds'].append(device['uuid'])
        except:
            pass
    return payload


def step2configInput(payload: dict) -> dict:
    '''
    Book devices for configuration push, returns the new device config
    '''
    print('=> Prepare device Config')
    response = session.postRequest(
        '/dataservice/template/device/config/input/', payload)
    return response.json()


def step3pushConfig(dTemAffected: list) -> dict:
    '''
    Push Configuration to devices
    '''
    finalPayload = {"deviceTemplateList": []}
    for template in dTemAffected:
        print(f"=> Configuring Device Template >> {template}")
        payload = step2payload(template)
        config = step2configInput(payload)['data']
        item = {"templateId": template, "device": config, "isEdited": True,
                "isMasterEdited": False}
        finalPayload['deviceTemplateList'].append(item)
        payload = None
        config = None
        item = None
    return finalPayload


def main(fTemName, update):
    '''
    This function put everthing together and push final config
    '''
    fTemId = getFTemIdByName(fTemName)
    dTemAffected = step1pushUpdate(fTemId, update)
    finalPayload = step3pushConfig(dTemAffected)
    response = session.postRequest(
        '/dataservice/template/device/config/attachfeature', finalPayload)
    print(response.text)


if __name__ == '__main__':
    fTemName = input('=> Enter the name of the feature template: ')
    fileName = input('=> Enter update filename in json format: ')
    update = openUpdateFile(fileName)
    main(fTemName, update)
