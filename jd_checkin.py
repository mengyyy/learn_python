#!/usr/bin/env python3
# -*-coding: utf-8-*-

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
import time
import logging
import signal

# 签到间隔
checkin_interval = 300 
username = '京东账号'
passwd = '京东密码'
# telegram 用户id
my_chatid = [12345678999]
chat_id = my_chatid[0]
# telegram bot token
my_token = '123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ'
screenshot_path = '/root/jd.png'
checkin_log_path = '/root/checkin_jd.log'
sms_code = '0'

dcap = dict(DesiredCapabilities.PHANTOMJS)
dcap["phantomjs.page.settings.userAgent"] = \
    "Mozilla/5.0 (Windows NT 5.1; rv:49.0) Gecko/20100101 Firefox/49.0"
phantomjsPath = '/root/phantomjs-2.1.1-linux-x86_64/bin/phantomjs'
login_url = 'https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fjr.jd.com%2F'
checkin_url = 'https://jr.jd.com/'
login_xpath = '//*[@id="content"]/div/div[1]/div/div[2]'
username_xpath = '//*[@id="loginname"]'
passwd_xpath = '//*[@id="nloginpwd"]'
login_click_xpath = '//*[@id="loginsubmit"]'

show_xpath = '//*[@id="viewNew"]'
checkin_xpath = '//*[@id="primeWrap"]/div[3]/div[3]/div[1]/a/span'
code_xpath = '//*[@id="code"]'
submit_code_xpath = '//*[@id="submitBtn"]'

# create logger with 'spam_application'
logger = logging.getLogger('jd_checkin')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(checkin_log_path)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


def start_driver():
    driver = webdriver.PhantomJS(
        executable_path=phantomjsPath, desired_capabilities=dcap)
    wait = WebDriverWait(driver, 30)
    driver.set_window_size(1280, 1024)
    return driver, wait


# jd check in start
def send_screenshot(bot, driver):
    try:
        ti = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
        driver.save_screenshot(screenshot_path)
        bot.send_photo(chat_id=chat_id, photo=open(screenshot_path, 'rb'))
        bot.send_document(
            chat_id=chat_id,
            document=open(screenshot_path, 'rb'),
            filename='{}.png'.format(ti),
            caption='{}'.format(ti))
    except:
        logger.error('send screen failed')


def send_log(logger, bot, st):
    ti = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logger.info(st)
    try:
        bot.send_message(chat_id=chat_id, text='{}--{}'.format(ti, st))
    except BaseException as e:
        logger.error(str(e))


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
            send_log(logger, bot, str(e))
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


def deal_jump_show(driver, wait, bot):
    driver.set_window_size(1280, 1024)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, show_xpath)))
    except:
        send_log(logger, bot, 'show_xpath failed')
    finally:
        send_screenshot(bot, driver)
    show_cnt = 0
    while driver.find_elements_by_xpath(show_xpath):
        logger.debug('found show_xpath')
        driver.find_element_by_xpath(show_xpath).click()
        time.sleep(2)
        show_cnt += 1
        logger.info('show_xpath click {} times'.format(show_cnt))
        if show_cnt > 60:
            send_log(logger, bot, 'click show_xpath too much')
            break


def deal_checkin(driver, wait, bot):
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, checkin_xpath)))
        driver.find_element_by_xpath(checkin_xpath).click()
        time.sleep(5)
        driver.find_element_by_xpath(checkin_xpath).click()
    except BaseException as e:
        send_log(logger, bot, str(e))
    finally:
        send_log(logger, bot, 'check in finish')
        send_screenshot(bot, driver)


def jdc_do(bot, update):
    driver, wait = start_driver()
    logger.debug('START (`\./`)')
    login_usrpwd(driver, wait, bot)
    if 'safe.jd.com' in driver.current_url:
        logger.debug('need sms code')
        deal_sms_code(driver, bot)
    else:
        driver.get(checkin_url)
    if 'jr.jd.com' in driver.current_url:
        logger.debug('deal jr.jd.com')
        deal_jump_show(driver, wait, bot)
    time.sleep(5)
    deal_checkin(driver, wait, bot)
    try:
        driver.service.process.send_signal(signal.SIGKILL)
        driver.quit()
    except:
        logger.error('driver quit failed')


def callback_jd(bot, update, args, job_queue, chat_data):
    # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-JobQueue
    if len(args) < 1:
        args = [str(JDC_INTERVAL)]
    logger.info('callback_jd args is {}'.format(args[0]))
    um_chat_id = update.message.chat_id
    if args[0] == 'stop':
        logger.info('try stop jd check in ')
        try:
            job = chat_data['job']
            job.schedule_removal()
            del chat_data['job']
        except Exception as e:
            logger.error('fail stop job {}'.format(repr(e)))
        else:
            logger.info('stop job successed')
            bot.send_message(chat_id=um_chat_id,
                             text='stop job successed')
    else:
        try:
            job_interval = int(args[0])
            if job_interval < 60:
                bot.send_message(chat_id=um_chat_id,
                                 text='喵？喵？喵？ >=60S')
                job_interval = 60
        except:
            bot.send_message(chat_id=um_chat_id,
                             text='interval arg error')
        else:
            if 'job' not in chat_data.keys():
                job = job_queue.run_repeating(jdc_do, job_interval, 2)
                chat_data['job'] = job
                logger.info(
                    'creat a new jdc_do job with interval {} S'.format(job_interval))
            else:
                job = chat_data['job']
                job.interval = job_interval
                logger.info('jdc_do job interval is {} S'.format(job_interval))

# jd check in end

def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Didn't understand that command.\n"
                    "Maybe you need a space between command and its args.")


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
