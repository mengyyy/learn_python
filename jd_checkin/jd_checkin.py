#! /usr/bin/python3
# -*- coding:utf-8 -*-
# pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  |
# xargs -n1 pip3 install -U

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import RegexHandler
import logzero
import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import subprocess
import signal
import json

with open('jd-config.json') as data_file:
    data = json.load(data_file)

chat_id = data['chat_id']
my_token = data['my_token']
JDC_INTERVAL = data['JDC_INTERVAL']
username = data['username']
passwd = data['passwd']

log_time_str = time.strftime('%Y_%m_%d_%H_%M', time.localtime())
checkin_log_path = '/home/Downloads/jd_jdc_{}.log'.format(log_time_str)
screenshot_path = '/root/jd.png'
sms_code = '0'

# firefox
geckodriver_path = '/home/Downloads/geckodriver'
options = Options()
options.add_argument("--headless")


login_url = 'https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fjr.jd.com%2F'
checkin_url = 'https://jr.jd.com/'
login_xpath = '//*[@id="content"]/div[2]/div[1]/div/div[3]'
username_xpath = '//*[@id="loginname"]'
passwd_xpath = '//*[@id="nloginpwd"]'
login_click_xpath = '//*[@id="loginsubmit"]'

show_xpath = '//*[@id="viewNew"]'
checkin_xpath = '//*[@id="primeWrap"]/div[1]/div[3]/div[1]/a/span'

code_xpath = '//*[@id="code"]'
submit_code_xpath = '//*[@id="submitBtn"]'

logPath = '/home/Downloads/LOG/jd_check.log'
logger = logzero.setup_logger(
    'jd_checkin', logfile=logPath, maxBytes=2**20, backupCount=10)


def start_driver(wait_time=10):
    driver = webdriver.Firefox(
        firefox_options=options, executable_path=geckodriver_path)
    wait = WebDriverWait(driver, wait_time)
    driver.set_window_size(1280, 1024)
    return driver, wait


def driver_kill(driver):
    try:
        driver.quit()
    except:
        logger.exception('driver quit failed---')


def send_screenshot(bot, driver):
    logger.info('start send screenshot')
    try:
        ti = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
        driver.save_screenshot(screenshot_path)
        bot.send_photo(chat_id=chat_id,
                       photo=open(screenshot_path, 'rb'),
                       timeout=60)
        bot.send_document(
            chat_id=chat_id,
            document=open(screenshot_path, 'rb'),
            filename='{}.png'.format(ti),
            caption='{}'.format(ti),
            timeout=60)
    except Exception as e:
        logger.exception('send screenshot failed')


def send_log(logger, bot, st):
    ti = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logger.info(st)
    try:
        bot.send_message(chat_id=chat_id, text='{}--{}'.format(ti, st))
    except Exception as e:
        logger.exception('message')


def get_sms_code(bot, update, args):
    global sms_code
    sms_code = args[0]
    bot.send_message(chat_id=chat_id, text='get_sms_code args {}'.format(args))


def get_checkin_log(bot, update, args):
    bot.send_message(
        chat_id=chat_id, text='get_checkin_log args {}'.format(args))
    with open(checkin_log_path, 'r') as f:
        data = f.read()[-1000:]
    bot.send_message(chat_id=chat_id, text=data)
    bot.send_document(chat_id=chat_id, document=open(checkin_log_path, 'rb'),
                      filename=os.path.basename(checkin_log_path))


def login_usrpwd(driver, wait, bot):
    login_cnt = 0
    while True:
        try:
            driver.delete_all_cookies()
            driver.get(login_url)
            wait.until(EC.presence_of_element_located((By.XPATH, login_xpath)))
            driver.find_element_by_xpath(login_xpath).click()
            wait.until(EC.presence_of_element_located(
                (By.XPATH, username_xpath)))
            wait.until(EC.presence_of_element_located(
                (By.XPATH, passwd_xpath)))
            wait.until(EC.presence_of_element_located(
                (By.XPATH, login_click_xpath)))
            driver.find_element(By.XPATH, username_xpath).clear()
            driver.find_element(By.XPATH, passwd_xpath).clear()
            driver.find_element(By.XPATH, username_xpath).send_keys(username)
            driver.find_element(By.XPATH, passwd_xpath).send_keys(passwd)
            driver.find_element_by_xpath(login_click_xpath).click()
            logger.debug('login finish~~~')
        except BaseException as e:
            send_log(logger, bot, 'login error accourt')
            send_screenshot(bot, driver)
            send_log(logger, bot, repr(e))
        time.sleep(5)
        login_cnt += 1
        if driver.current_url != login_url or login_cnt > 5:
            break


def deal_sms_code(driver, bot, t=40):
    try:
        send_screenshot(bot, driver)
        bot.send_message(chat_id=chat_id, text='/sms_code xxxxx')
        time.sleep(t)
        logger.debug('time out use code {}'.format(sms_code))
        driver.find_element(By.XPATH, code_xpath).send_keys(sms_code)
        driver.find_element_by_xpath(submit_code_xpath).click()
    except BaseException as e:
        send_screenshot(bot, driver)
        send_log(logger, bot, str(e))


def deal_checkin(driver, wait, bot):
    status_text = ''
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, checkin_xpath)))
        status_text = driver.find_element_by_xpath(checkin_xpath).text
        send_log(logger, bot, 'checkined | {}'.format(status_text))
        time.sleep(5)
        driver.find_element_by_xpath(checkin_xpath).click()
    except BaseException as e:
        send_log(logger, bot, repr(e))
    finally:
        if status_text != '今日已签':
            send_log(logger, bot, 'new checkin')
            send_screenshot(bot, driver)


def jdc_do(bot, update):
    try:
        logger.debug('START (`\./`)')
        driver, wait = start_driver()
        login_usrpwd(driver, wait, bot)
        if 'safe.jd.com' in driver.current_url:
            logger.debug('need sms code')
            deal_sms_code(driver, bot)
        else:
            driver.get(checkin_url)
        if 'jr.jd.com' in driver.current_url:
            logger.debug('deal jr.jd.com')
        time.sleep(5)
        deal_checkin(driver, wait, bot)
    except Exception as e:
        logger.exception('message')
    finally:
        driver_kill(driver)


def callback_jd(bot, update, args, job_queue, chat_data):
    # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-JobQueue
    if len(args) < 1:
        args = [str(JDC_INTERVAL)]
    logger.info('callback_jd args is {}'.format(args[0]))
    if args[0] == 'stop':
        logger.info('try stop jd check in ')
        update.message.reply_text('try stop jd check in ')
        try:
            job = chat_data['job']
            job.schedule_removal()
            del chat_data['job']
        except Exception as e:
            logger.error('fail stop job {}'.format(repr(e)))
        else:
            logger.info('stop job successed')
            update.message.reply_text('stop job successed')
    else:
        try:
            job_interval = int(args[0])
            if job_interval < 3600:
                update.message.reply_text('喵？喵？喵？ >=3600S')
                job_interval = 3600
        except:
            update.message.reply_text('interval arg error')
        else:
            if 'job' not in chat_data.keys():
                job = job_queue.run_repeating(jdc_do, job_interval, 2)
                chat_data['job'] = job
                info = 'creat a new jdc_do job with interval {} S'.format(
                    job_interval)
                logger.info(info)
                update.message.reply_text(info)
            else:
                job = chat_data['job']
                job.interval = job_interval
                info = 'jdc_do job interval is {} S'.format(job_interval)
                logger.info(info)
                update.message.reply_text(info)


def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Didn't understand that command.\n"
                    "Maybe you need a space between command and its args.")


def main():
    bot = telegram.Bot(my_token)
    bot.send_message(chat_id=chat_id, text='Send me /jdc to start')
    updater = Updater(token=my_token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('sms_code', get_sms_code, pass_args=True))
    dp.add_handler(CommandHandler('log', get_checkin_log, pass_args=True))
    dp.add_handler(CommandHandler('jdc', callback_jd,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
