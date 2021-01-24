# coding=utf-8
__author__ = 'kupr'
import os

t = os.popen('ps  -C "python" -o pid,command').read().split('\n')
isDone = False
for x in t:
    if x.find('museum.py') > 0:
        if int(x.split()[0]) != int(os.getpid()) :
            isDone = True

if not isDone :
    import time
    import logs
    import m_actions
    logs.log.writelog('Запуск museum ')
    states = m_actions.States()
    states.Reset()

    while True :
        states.RunProcess()
        states.PoolSensors()
        states.TestCommand()
        time.sleep(0.1)
