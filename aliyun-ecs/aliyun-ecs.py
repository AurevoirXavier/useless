# --- std ---
from datetime import datetime, timedelta
from time import sleep
# --- external ---
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import \
    AllocatePublicIpAddressRequest, \
    CreateInstanceRequest, \
    DescribeZonesRequest, \
    ModifyInstanceAutoReleaseTimeRequest, \
    StartInstanceRequest
from json import loads
# --- custom ---
from secret import *


def describe_zones(client):
    req = DescribeZonesRequest.DescribeZonesRequest()
    req.set_accept_format('json')

    return loads(client.do_action(req))


def create_instance(client):
    req = CreateInstanceRequest.CreateInstanceRequest()
    req.set_ZoneId(ZONE_ID)
    req.set_SecurityGroupId(SECURITY_GROUP_ID)
    req.set_ImageId(IMAGE_ID)
    req.set_VSwitchId(V_SWITCH_ID)

    req.set_InstanceType(INSTANCE_TYPE)
    req.set_IoOptimized(IO_OPTIMIZED)
    req.set_SystemDiskCategory(SYSTEM_DISK_CATEGORY)
    req.set_SystemDiskSize(SYSTEM_DISK_SIZE)

    req.set_InternetChargeType('PayByTraffic')
    req.set_InternetMaxBandwidthIn(UPLOAD_BAND_WIDTH)
    req.set_InternetMaxBandwidthOut(DOWNLOAD_BAND_WIDTH)

    req.set_SpotStrategy('SpotWithPriceLimit')
    req.set_SpotPriceLimit(STOP_PRICE_LIMIT)

    req.set_accept_format('json')

    return loads(client.do_action(req))


def modify_instance_release_time(client, instance_id):
    time = (datetime.utcnow() + timedelta(minutes=55)).strftime('%Y-%m-%dT%H:%M:%SZ')
    print(f'Auto release time: {time}')

    req = ModifyInstanceAutoReleaseTimeRequest.ModifyInstanceAutoReleaseTimeRequest()
    req.set_InstanceId(instance_id)
    req.set_AutoReleaseTime(time)
    req.set_accept_format('json')

    return loads(client.do_action(req))


def start_instance(client, instance_id):
    req = StartInstanceRequest.StartInstanceRequest()
    req.set_InstanceId(instance_id)
    req.set_accept_format('json')

    return loads(client.do_action(req))


def allocate_public_ip_address(client, instance_id):
    req = AllocatePublicIpAddressRequest.AllocatePublicIpAddressRequest()
    req.set_InstanceId(instance_id)
    req.set_accept_format('json')

    resp = loads(client.do_action(req))
    return resp['IpAddress']


def wait(tips, time):
    for i in range(time, 0, -1):
        print(f'\r{tips}: {i}s', end='')
        sleep(1)


def start_create_instance(client):
    while True:
        resp = create_instance(client)

        if 'Code' in resp:
            if resp['Code'] == 'InvalidSpotPriceLimit.LowerThanPublicPrice':
                print('Lower than public price, wait 60s')
                sleep(60)
            else:
                print(resp)
                raise ValueError
        else:
            break

    instance_id = resp['InstanceId']
    print(f'Instance id: {instance_id}')
    modify_instance_release_time(client, instance_id)
    wait('Allocating', 30)
    print('\rAllocating succeed')
    start_instance(client, instance_id)
    wait('Booting', 90)
    print('\rBooting succeed')
    ip_address = allocate_public_ip_address(client, instance_id)
    print(f'\rIp address: {ip_address}')


if __name__ == '__main__':
    client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION_ID)
    for _ in range(LOOP):
        start_create_instance(client)
        sleep(WAIT)
