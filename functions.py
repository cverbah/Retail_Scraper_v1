import time
import numpy as np
import unidecode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException

##functions
def preprocess_text(text):
    ''''preprocess a string to lower cap and remove special accents.'''
    text = unidecode.unidecode(text).lower()
    return text

def get_product_data(driver, sku):
    '''get the info from the product. Currently some settings for Quillota (store_stock)
       input: webdriver, sku
       ouput: dictionary with product info
    '''
    search_bar = driver.find_element(By.ID, "testId-SearchBar-Input")
    search_bar.click()

    search_bar.send_keys(str(sku))
    search_bar.send_keys(Keys.ENTER)
    time.sleep(1)

    # info de producto:
    product = {}

    sku_url = driver.current_url
    product['url'] = sku_url
    product['sku'] = int(sku)
    # descripcion
    try:
        description = driver.find_element(By.CLASS_NAME, 'jsx-1442607798').text
        product['descripcion'] = preprocess_text(description)
    except:
        product['descripcion'] = np.nan
    
    # check stock in website
    try:
        check_stock_web = driver.find_element(By.ID, 'testId-product-outofstock')
        product['stock_en_website'] = False

    except:
        product['stock_en_website'] = True

    # price
    try:
        class_name_prices = 'prices-4_GRID'
        price_element = driver.find_element(By.CLASS_NAME, class_name_prices)

        prices = price_element.text
        prices = prices.replace('$','')
        prices = prices.split()

        if len(prices) == 1:
            price = int(eval(prices[0]) * 1000)
            product['precio'] = price
            product['precio_dcto'] = np.nan
            product['precio_cmr'] = np.nan

        if len(prices) == 2: #porsiaca??

            price, price_dcto = int(eval(prices[1]) * 1000), int(eval(prices[0]) * 1000)
            product['precio'] = price
            product['precio_dcto'] = price_dcto
            product['precio_cmr'] = np.nan


        if len(prices) == 3:
            # buscar si cmr o no
            class_name_aux = 'prices-0'
            type_element = driver.find_element(By.CLASS_NAME, class_name_aux)

            if type_element.get_attribute('data-event-price'):
                price, dcto, price_dcto = int(eval(prices[2]) * 1000), str(prices[1]), int(eval(prices[0]) * 1000)
                product['precio'] = price
                product['precio_dcto'] = price_dcto
                product['precio_cmr'] = np.nan

            if type_element.get_attribute('data-cmr-price'):
                price, dcto, price_cmr = int(eval(prices[2]) * 1000), str(prices[1]), int(eval(prices[0]) * 1000)
                product['precio'] = price
                product['precio_dcto'] = np.nan
                product['precio_cmr'] = price_cmr


        if len(prices) == 4:
            price_cmr, price, price_dcto = int(eval(prices[0]) * 1000), int(eval(prices[3]) * 1000), int(eval(prices[2]) * 1000)
            product['precio'] = price
            product['precio_dcto'] = price_dcto
            product['precio_cmr'] = price_cmr

    except:
        product['precio'] = np.nan
        product['precio_dcto'] = np.nan
        product['precio_cmr'] = np.nan
        product['stock_en_website'] = np.nan

    # codigo_producto, codigo tienda
    codes = ['codigo del producto', 'cod. tienda']
    try:
        for i in driver.find_elements(By.CLASS_NAME, "jsx-3410277752"):
            tipo_cod, code = i.text.split(': ')
            tipo_cod = preprocess_text(tipo_cod)
            code = int(code)
            product[tipo_cod] = code

        for code_name in codes:
            if code_name in list(product.keys()):
                continue

            elif code_name not in list(product.keys()):
                product[code_name] = np.nan

    except:

        for code_name in codes:
            if code_name in list(product.keys()):
                continue

            elif code_name not in list(product.keys()):
                product[code_name] = np.nan

    try:
        check_stock_store = driver.find_element(By.ID, 'testId-open-store-availability-modal-desktop')
        try:
            check_stock_store.click()

        except ElementClickInterceptedException:

            driver.execute_script("arguments[0].click();", check_stock_store)

        # info de stock en tienda homecenter quillota
        time.sleep(3)
        region = driver.find_elements(By.CLASS_NAME, 'Autocomplete-module_autocomplete-input-wrapper__3WjSy')[0].click()
        selected_region = driver.find_element(By.XPATH,
                                              '//*[@id="zone_modal_wrap"]/div/div/div/div[2]/div[1]/div/div/ul/li[16]').click()
        time.sleep(2)

        comuna = driver.find_elements(By.CLASS_NAME, 'Autocomplete-module_autocomplete-input-wrapper__3WjSy')[1].click()
        selected_comuna = driver.find_element(By.XPATH,
                                              '//*[@id="zone_modal_wrap"]/div/div/div/div[2]/div[2]/div/div/ul/li[56]').click()
        time.sleep(2)

        #
        check_stock_store = driver.find_element(By.ID, 'testId-select-stock')
        try:
            check_stock_store.click()

        except ElementClickInterceptedException:

            driver.execute_script("arguments[0].click();", check_stock_store)
        time.sleep(2)

        try:
            store_location = driver.find_element(By.XPATH, '//*[@id="testId-store-item"]/div[2]/div/p/span').text
            product['tienda'] = preprocess_text(store_location)
            store_stock = driver.find_element(By.XPATH, '//*[@id="testId-store-item"]/div[2]/p[2]').text
            store_stock = int(store_stock.split(' ')[0])
            product['stock_en_tienda'] = store_stock

        except:
            product['tienda'] = np.nan
            product['stock_en_tienda'] = np.nan

        # close window
        driver.find_element(By.ID, 'testId-modal-close').click()

    except:
        product['tienda'] = np.nan
        product['stock_en_tienda'] = np.nan


    curr_time = time.strftime("%D %H:%M:%S", time.localtime())
    product['snapshot'] = curr_time

    print(product)
    return product

