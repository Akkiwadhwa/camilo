from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_driver():
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    #chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chrome_install = ChromeDriverManager().install()

    folder = os.path.dirname(chrome_install)
    chromedriver_path = os.path.join(folder, "chromedriver.exe")

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login(driver, rut, clave):
    """Log into the SII portal using the provided credentials."""
    url = 'https://misiir.sii.cl/cgi_misii/siihome.cgi'
    driver.get(url)
    driver.implicitly_wait(10)

    # Locate and fill out login fields
    driver.find_element(By.ID, "rutcntr").send_keys(rut)
    driver.find_element(By.ID, "clave").send_keys(clave)
    driver.find_element(By.ID, "bt_ingresar").click()

def is_logged(driver, timeout=3):
    """Check if the login was successful by verifying the current URL."""
    try:
        boton_xpath = "//a[contains(text(), 'Continuar') and contains(@class, 'btn-primary')]"
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, boton_xpath))
        )
        return True
    except Exception:
        return driver.current_url != 'https://zeusr.sii.cl/cgi_AUT2000/CAutInicio.cgi'

def get_address(driver):
    try:
        address_element = driver.find_element(By.ID, 'domiCntr')
        address = address_element.text
    except NoSuchElementException:
        logging.error("No se pudo obtener la dirección")
        return None
    logging.info(f'Dirección obtenida: {address}')
    return address

def get_name(driver):
    try:
        name_element = driver.find_element(By.ID, 'nameCntr')
        name = name_element.text
    except NoSuchElementException:
        logging.error("No se pudo obtener el nombre")
        return None
    logging.info(f'Nombre obtenido: {name}')
    return name

def get_email(driver):
    try:
        email_contacto_element = driver.find_element(By.ID, 'mailCntr')
        email = email_contacto_element.text
        if email == '':
            try:
                email_contacto_element = driver.find_element(By.ID, 'mailCntrNoti')
                email = email_contacto_element.text
            except NoSuchElementException:
                return None
    except NoSuchElementException:
        return None
    return email

def select_form_and_period(driver, year, month):
    """Select the appropriate form and the period (year and month)."""
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//select[@class="gwt-ListBox"]'))
        )

        # Select "Formulario 29" for the form, year, and month
        Select(driver.find_element(By.XPATH, '//select[@class="gwt-ListBox"]')).select_by_visible_text("Formulario 29")
        Select(driver.find_elements(By.XPATH, '//select[@class="gwt-ListBox"]')[1]).select_by_visible_text(year)
        time.sleep(3)
        Select(driver.find_elements(By.XPATH, '//select[@class="gwt-ListBox"]')[2]).select_by_visible_text(month)
    except NoSuchElementException:
        logging.error(f"Could not find form or period elements for year: {year}, month: {month}")
        return False
    return True

def click_search_button(driver):
    try:
        search_button = driver.find_element(By.XPATH, '//button[@class="gwt-Button" and @title="Presione aquí para desplegar datos previamente ingresados para el formulario y período seleccionado."]')
        search_button.click()
    except NoSuchElementException:
        return False
    return True

def get_folio_and_navigate(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//table[@class="tabla_internet" and .//td[text()="DECLARACIONES VIGENTES"]]'))
        )
        folio_element = driver.find_element(By.XPATH, '//table[@class="tabla_internet" and .//td[text()="DECLARACIONES VIGENTES"]]//tr/td/div[@class="gwt-Hyperlink"]/a')
        folio = folio_element.text
    except NoSuchElementException:
        return None
    return folio

def extract_value_for_code(driver, target_code):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//table[@class="borde_tabla_f29_xslt noleft"]'))
    )
    try:
        code_element = driver.find_element(By.XPATH, f'//td[@class="celda-codigo" and text()="{target_code}"]')
        value_element = code_element.find_element(By.XPATH, './following-sibling::td[@class="tabla_td_fixed_b_right"]')
        value_text = value_element.text.strip()
    except NoSuchElementException:
        return None
    return value_text

def scrape_data_for_account(rut, clave, year, month, target_codes):
    """Main function to log in, select the form and period, and scrape data."""
    logging.info('Iniciando driver...')
    driver = initialize_driver()
    account_results = {}
    account_results["RUTF"] = rut
    logging.info('Driver iniciado.')
    try:
        logging.info('Log In...')
        login(driver, rut, clave)
        if not is_logged(driver):
            logging.info('Cuenta no logeada.')
            raise Exception("Login failed")
        driver.get("https://misiir.sii.cl/cgi_misii/siihome.cgi")
        logging.info('Obteniendo dirección...')
        account_results["NOMBRE"] = get_name(driver)
        account_results["DIRECCION"] = get_address(driver)
        account_results["CORREO"] = get_email(driver)
        driver.get("https://www4.sii.cl/rfiInternet/consulta/index.html#rfiSelFormularioPeriodo")
        if not select_form_and_period(driver, year, month):
            return account_results
        if not click_search_button(driver):
            return account_results
        account_results["FOLIO"] = get_folio_and_navigate(driver)
        folio = account_results["FOLIO"]
        if not folio:
            return account_results
        driver.get(f'https://www4.sii.cl/rfiInternet/?opcionPagina=formCompleto&folio={folio}&form=29')
        if folio:
            for code in target_codes:
                value = extract_value_for_code(driver, code)
                account_results[code] = value
        account_results["RETENCION"] = get_retencion(driver=driver, month=month, year=year)
        logging.info(f"Successfully scraped data for {rut} for period {year}-{month}")
        return account_results
    except Exception as e:
        logging.error(f"Error during scraping for {rut}: {str(e)}")
        raise
    finally:
        driver.quit()

def get_retencion(driver, month, year):
        try:
            driver.get('https://loa.sii.cl/cgi_IMT/TMBCOC_MenuConsultasContribRec.cgi?dummy=1461943244650')
            time.sleep(5)
            month_dropdown = driver.find_element(By.ID, "select")
            month_select = Select(month_dropdown)
            month_select.select_by_visible_text(month)
            time.sleep(1)
            year_dropdown = driver.find_element(By.XPATH, "//select[@name='cbanoinformemensual']")
            year_select = Select(year_dropdown)
            year_select.select_by_visible_text(year)
            time.sleep(1)
            driver.find_element(By.ID, "cmdconsultar1").click()
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//form[1]//table[1]")))
            time.sleep(1)
            txt = driver.find_element(By.XPATH, "/html/body/div[2]/center/center/form[1]/table/tbody/tr[last()]/td[3]").text.strip()
            return txt
        except Exception as e: 
            print(e)

        return ''

#check f22 status
def check_f22_status(rut, clave, year):
    """Log in, select the form and period, and scrape data."""
    logging.info('Iniciando driver...')
    driver = initialize_driver()
    account_results = {}
    account_results["RUTF"] = rut
    logging.info('Driver iniciado.')
    try:
        logging.info('Log In...')
        login(driver, rut, clave)
        if not is_logged(driver):
            logging.info('Cuenta no logeada.')
            account_results["NOMBRE"] = "CLAVE INCORRECTA"
            return account_results
        driver.get("https://misiir.sii.cl/cgi_misii/siihome.cgi")
        logging.info('Obteniendo nombre...')
        account_results["NOMBRE"] = get_name(driver)
        logging.info('Cargando https://www4.sii.cl/consultaestadof22ui...')
        driver.get("https://www4.sii.cl/consultaestadof22ui")
        time.sleep(1)
        logging.info('Navegando en el sitio...')
        if not select_year_consultaestadof22ui(driver, year):
            return account_results
        if not click_consultar_button(driver):
            return account_results
        account_results["SITUACION"] = get_situacion_renta_actual(driver)
        if(account_results["SITUACION"].startswith("Actualmente") or account_results["SITUACION"].startswith("Tus datos")):
            return account_results
        account_results["FOLIO"] = get_folio_from_historial(driver)
        if not click_formulario_compacto(driver):
            return account_results
        time.sleep(5)
        account_results["MONTO DEVOLUCION"] = get_info_from_f22_compacto(driver, 87)
        account_results["MONTO A PAGAR"] = get_info_from_f22_compacto(driver, 91)
        logging.info(f"Successfully scraped data for {rut} for period {year}")
        return account_results
    except Exception as e:
        logging.error(f"Error during scraping for {rut}: {str(e)}")
        raise
    finally:
        driver.quit()
    pass

def select_year_consultaestadof22ui(driver, year):
    """Select the appropriate form and the period (year)."""
    logging.info("Intentando encontrar el select")
    try:
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[data-ng-model='vm.selectedOption']"))
        )

        select = Select(select_element)
        select.select_by_visible_text(year)
        time.sleep(2)
    except NoSuchElementException:
        logging.error(f"Could not find form or period elements for year: {year}")
        return False
    return True
    pass

def click_consultar_button(driver):
    try:
        search_button = driver.find_element(By.XPATH, '//*[@id="formulario-periodo"]/div/div[2]/div/button')
        search_button.click()
    except NoSuchElementException:
        return False
    return True

def get_situacion_renta_actual(driver, timeout=10):
    try:
        # Esperar a que aparezca alguno de los dos: el span o el mensaje en el alert
        WebDriverWait(driver, timeout).until(lambda d: (
            d.find_element(By.XPATH, "//div[@id='SituacionActual']//span[@ng-bind-html='situacionActual']").is_displayed() or
            d.find_element(By.XPATH, "//div[@id='SituacionActual']//div[contains(@class, 'alert-sin-situacion')]//p").is_displayed()
        ))

        # Intentar extraer el texto del span si está visible y tiene texto
        try:
            span = driver.find_element(By.XPATH, "//div[@id='SituacionActual']//span[@ng-bind-html='situacionActual']")
            if span.is_displayed() and span.text.strip():
                return span.text.strip()
        except:
            pass

        # Intentar extraer el texto del mensaje dentro de la alerta si está visible
        try:
            p = driver.find_element(By.XPATH, "//div[@id='SituacionActual']//div[contains(@class, 'alert-sin-situacion')]//p")
            if p.is_displayed():
                return p.text.strip()
        except:
            pass

        return "Mensaje no visible o vacío"

    except Exception as e:
        print(f"❌ Error al obtener situación: {e}")
        return "Error al obtener situación"

def click_formulario_compacto(driver):
    try:
        search_button = driver.find_element(By.XPATH, '//*[@id="my-wrapper"]/div[3]/div/div/div/div/div[1]/div[6]/button[3]')
        search_button.click()
    except NoSuchElementException:
        return False
    return True

def get_folio_from_historial(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//small[contains(text(), 'Folio')]/span"))
        )
        folio_element = driver.find_element(By.XPATH, "//small[contains(text(), 'Folio')]/span")
        folio = folio_element.text.strip()
    except NoSuchElementException:
        return None
    return folio

def get_info_from_f22_compacto(driver, code, timeout=10):
    WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//div[contains(@class, 'col-codigo') and normalize-space(text())='{code}']")
            )
        )

    try:
        code_elements = driver.find_elements(By.CSS_SELECTOR, '.col-codigo.bg-orange.div-cell.bleft-codigo')
        for code_element in code_elements:
            if code_element.text.strip() == str(code):
                contenedor = code_element.find_element(By.XPATH, './..')
                value_element = contenedor.find_element(By.CSS_SELECTOR, '.col-valor.div-cell.ng-binding')
                value_text = value_element.text.strip()
                break
    except NoSuchElementException:
        return None
    return value_text


# check password
def check_password_account(rut, clave):
    """Main function to log in and check if password is correct."""
    logging.info('Iniciando driver...')
    driver = initialize_driver()
    account_results = {}
    account_results["RUTF"] = rut
    logging.info('Driver iniciado.')
    try:
        logging.info('Log In...')
        login(driver, rut, clave)
        if is_logged(driver):
            account_results["ESTADO"] = "CORRECTA"
        else:
            account_results["ESTADO"] = "INCORRECTA"
        return account_results
    except Exception as e:
        logging.error(f"Error during scraping for {rut}: {str(e)}")
        raise
    finally:
        driver.quit()

# get ddjj
def esperar_tabla_con_encabezado_dj(driver, timeout=15):
    """
    Espera a que la tabla dentro del div .data-container esté cargada
    y que el primer <th> del thead sea 'DJ'. Retorna el WebElement de la tabla.
    """

    def tabla_lista(driver):
        try:
            contenedor = driver.find_element(By.CLASS_NAME, "data-container")
            tabla = contenedor.find_element(By.TAG_NAME, "table")
            th_elements = tabla.find_elements(By.CSS_SELECTOR, "thead th")
            return th_elements and th_elements[0].text.strip() == "DJ"
        except:  # noqa: E722
            return False

    WebDriverWait(driver, timeout).until(tabla_lista)

    # Si pasó el wait, devolvemos la tabla
    return True

def get_years(driver):
    years = []
    contenedor = driver.find_element(By.CLASS_NAME, "data-container")
    tabla = contenedor.find_element(By.TAG_NAME, "table")
    th_elements = tabla.find_elements(By.CSS_SELECTOR, "thead th")
    
    for th in th_elements:
        texto = th.text.strip()
        if texto.isdigit():
            years.append(texto)

    return years

def get_ddjj_data(driver, years):
    data = []
    contenedor = driver.find_element(By.CLASS_NAME, "data-container")
    tabla = contenedor.find_element(By.TAG_NAME, "table")
    tbody = tabla.find_element(By.TAG_NAME, "tbody")
    filas = tbody.find_elements(By.TAG_NAME, "tr")

    for fila in filas:
        celdas = fila.find_elements(By.TAG_NAME, "td")
        if not celdas or len(celdas) < 2 + len(years):
            continue

        codigo_dj = celdas[0].text.strip()

        for idx, anio in enumerate(years):
            estado = celdas[2 + idx].text.strip() if 2 + idx < len(celdas) else ""
            data.append({
                "DJ": codigo_dj,
                "Ano": anio,
                "Estado": estado
            })
    
    return data

def get_ddjj_table(rut, clave):
    """Main function to log in and check if password is correct."""
    logging.info('Iniciando driver...')
    driver = initialize_driver()
    account_results = {}
    account_results["RUTF"] = rut
    logging.info('Driver iniciado.')
    try:
        logging.info('Log In...')
        login(driver, rut, clave)
        if not is_logged(driver):
            logging.info('Cuenta no logeada.')
            raise Exception("Login failed")
        driver.get("https://misiir.sii.cl/cgi_misii/siihome.cgi")
        logging.info('Obteniendo nombre...')
        account_results["NOMBRE"] = get_name(driver)
        account_results["CORREO"] = get_email(driver)
        driver.get("https://www2.sii.cl/djconsulta/estadoddjjs")
        try:
            tabla = esperar_tabla_con_encabezado_dj(driver)
        except:   # noqa: E722
            driver.quit()
        
        if tabla:
            years = get_years(driver)
            data = get_ddjj_data(driver, years)
        if data:
            for item in data:
                account_results[f"{item['DJ']}-{item['Ano']}"] = item['Estado']
        logging.info(f"Successfully scraped data for {rut}")
        print(account_results)
        return account_results
    except Exception as e:
        logging.error(f"Error during scraping for {rut}: {str(e)}")
        raise
    finally:
        driver.quit()