import pytest
from pulse import check_service, PulseConfig, Service, run_pulse

@pytest.mark.asyncio
async def test_check_service_up():
    service = Service(name='test', url='http://httpbin.org/status/200')
    result = await check_service(service)
    assert result['status'] == 'UP'

@pytest.mark.asyncio
async def test_check_service_down():
    service = Service(name='down', url='http://127.0.0.1:59999')
    result = await check_service(service)
    assert result['status'] == 'DOWN'

@pytest.mark.asyncio
async def test_run_pulse():
    config = PulseConfig(services=[Service(name='httpbin', url='http://httpbin.org/status/200')])
    result = await run_pulse(config)
    assert result['total'] == 1
    assert result['up'] == 1
