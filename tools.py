from patchright.async_api import Page
from bs4 import BeautifulSoup
import regex as re
import asyncio
import faiss
import json
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
import random

embeddings = HuggingFaceEmbeddings(

    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={'device': 'cuda'},
    encode_kwargs = {'normalize_embeddings' : True}  
)


#helper function for clickin
def build_selector(infos):
    all_selectors = []

    for info in infos:
        tag = info.get("tag", "").lower() or "*"
        id_ = info.get("id")
        class_ = info.get("class")
        name = info.get("name")
        type_ = info.get("type")
        value = info.get("value")
        text = info.get("text")
        placeholder = info.get("placeholder")
        title = info.get("title")
        alt = info.get("alt")
        href = info.get("href")
        role = info.get("role")
    
        selector_parts = [tag]

        if id_:
            selector_parts.append(f"#{id_.strip()}")

        elif class_:
            classes = [c.strip() for c in class_.split() if c and len(c) < 20 and c.lower() not in {"btn", "button", "input", "form"}]
            if classes:
                selector_parts.append("." + ".".join(classes[:2]))  

        if name:
            selector_parts.append(f'[name="{name.strip()}"]')

        for attr_name, attr_value in {
            "type": type_,
            "placeholder": placeholder,
            "title": title,
            "alt": alt,
            "role": role,
            "href": href
        }.items():
            if attr_value:
                safe_value = attr_value.replace('"', '\\"').strip()
                selector_parts.append(f'[{attr_name}="{safe_value}"]')

        selector = "".join(selector_parts)

        if text and len(text) < 40:
           
            text_value = re.sub(r'\s+', ' ', text.strip())
          
            text_value = text_value.replace('"', '\\"')
            selector += f':has-text("{text_value}")'

        info["selector"] = selector
        all_selectors.extend(info)

    return all_selectors


# google search donee
async def search_google(page:Page, query:list):
    if "https://www.google.com/" not in str(page.url):
        await page.goto('https://www.google.com/')

    search_box = page.locator("textarea#APjFqb")
    text_value = await search_box.input_value()

    await search_box.hover()
    await asyncio.sleep(random.uniform(0.5, 1))
    await search_box.click()
    await asyncio.sleep(random.uniform(0.5, 1))
    if text_value.strip():
        await page.keyboard.press('ControlOrMeta+A')
        await asyncio.sleep(random.uniform(0.5, 1))
        await page.keyboard.press('Backspace')
    
    temp_query = query[0]
    while isinstance(temp_query, list) and temp_query:
        temp_query = temp_query[0]
    await search_box.type(temp_query, delay=50)
    await search_box.press("Enter")

    await page.wait_for_load_state("domcontentloaded", timeout= 10000)
    await page.wait_for_load_state("networkidle")
    return ("visited :" + str(page.url))

# website search done
async def search_website(page:Page, query:list):
    search_icon = page.locator('span[class = "leadingIcon"]')
    count = await search_icon.count()
    if count > 0:
         await search_icon.hover()
         await asyncio.sleep(random.uniform(1,2))
         await search_icon.click()

    search = page.get_by_placeholder("Search").first
    await search.hover()
    await asyncio.sleep(random.uniform(1,2))
    await search.click()
    await search.fill("")
    await search.type(query[0], delay=50)
    await search.press("Enter")

    await page.wait_for_load_state("domcontentloaded")
    return ("visited" + str(page.url))  

#search_page links done
async def get_google_page_links(page:Page, why:list): 
    results = []
    links = page.locator("a")
    items = await links.evaluate_all(
        """
        elements => elements.map(ele =>({
            text : ele.innerText.trim(),
            href : ele.href
        }))
        """
    )
    for item in items:
        results.append({item["text"] : item["href"]})
    return results

#goto_page
async def goto_link(page:Page, url:list):
    URL = url[0]
    links = await get_google_page_links(page=page, why=[])
    for link in links:
        if URL in link.values():
            final_link = page.locator(f'a[href="{URL}"]')

            await final_link.first.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.5, 1))
            await final_link.first.hover()
            await asyncio.sleep(random.uniform(0.5, 1))
            await final_link.first.click()
            
            await page.wait_for_load_state("domcontentloaded", timeout= 10000)
            return ("visited : " + str(url[0]))
        
    await page.goto(URL)
    await page.wait_for_load_state("domcontentloaded", timeout= 10000)
    await asyncio.sleep(2)
    return ("visited : " + str(URL))

#getting a page text
async def get_page_text(page:Page, why:list):
    
    page_html =await  page.content()
    soup = BeautifulSoup(page_html, 'html.parser')
    text = soup.get_text().strip()
    text = re.sub(r'\n+', '\n',text)

    return ("extracted : \n" + text)

# writing to context
async def write_to_context(page:Page, text:list):
    context_file = open("context.txt", 'a', encoding='utf-8')
    context_file.write(str(text) + "\n\n")
    context_file.close()

    return ("wrote : " + str(text[0]))

#asking user
async def ask_user(page:Page, query:list):
     user_response = input(query[0])
     return ("user responded with : " + user_response)

#helper function for ui elements
async def get_all_ui_elements(page: Page):
    
    elements = ["a", "button", "input", "select", "textarea", "form", "[role='button']", "[role='link']", "[onclick]", "label"]
   
    interactive_list = []
    for element in elements:
        temp_locators = page.locator(element)
        result = await temp_locators.evaluate_all("""
        (tags) => tags.map(n => ({
            tag: n.tagName,
            id: n.id || null,
            class: n.className || null,
            name: n.getAttribute('name'),
            type: n.getAttribute('type'),
            value: n.value || null,
            text: n.innerText?.trim() || null,
            placeholder: n.getAttribute('placeholder'),
            title: n.getAttribute('title'),
            alt: n.getAttribute('alt'),
            href: n.getAttribute('href'),
            role: n.getAttribute('role')
            }))
        """)
        temp_selector = build_selector(result)
        print(temp_selector)
        interactive_list.extend(result)
    
    return interactive_list

#finding the UI tags etc
async def get_ui_element(page:Page, query:list):
    descriptions = []
    element_map = []
    quest = query[0]

    interactables = await get_all_ui_elements(page=page)

    for el in interactables:
        if el["tag"] == "INPUT":
            desc = f"Input field with placeholder '{el.get('placeholder')}' and current value '{el.get('value')}'"
        elif el["tag"] == "TEXTAREA":
            desc = f"Textarea with placeholder '{el.get('placeholder')}' and current value '{el.get('value')}'"
        elif el["tag"] == "SELECT":
            desc = f"Dropdown/select element with text '{el['text']}' and class attr'"
        elif el["tag"] == "FORM":
            desc = f"Form element with id '{el['id']}'"
        else:
            desc = f"{el['tag']} element with text '{el['text']}'"

        descriptions.append(desc)
        element_map.append(el)
    
    doc_embeddings = np.array(embeddings.embed_documents(descriptions), dtype="float32")
    doc_embeddings /= np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

    index = faiss.IndexFlatIP(doc_embeddings.shape[1])
    index.add(doc_embeddings)

    q_emb = np.array(embeddings.embed_query(quest), dtype="float32")
    q_emb /= np.linalg.norm(q_emb)
  
   

    similar_ui = []

    q_emb = np.array([embeddings.embed_query(quest)], dtype="float32")
    D, I = index.search(q_emb, k=3)
    for dist, idx in zip(D[0], I[0]):
        similar_ui.append({
            "description": descriptions[idx],
            "selector": element_map[idx],
            "similarity": float(dist)
        })

    return similar_ui

# filling thing
async def click_thing(page:Page, args:list):
    selector = args[0]
    await page.locator(selector).click()

    return ("clicked + " + str(selector))


async def fill_thing(page:Page, args:list):
    selector = args[0]
    text = args[1]
    form = page.locator(selector=selector)
    await form.type(text, delay=50)
    return ("typed " + text)


async def run_tool_function(page: Page, raw_output):
    if isinstance(raw_output.content, list):
        content_str = "\n".join(raw_output.content)
    else:
        content_str = raw_output.content
   
    cleaned = re.sub(r"```[a-zA-Z]*", "", content_str).strip()

    match = re.search(r"{.*}", cleaned, re.DOTALL)
    if match:
        json_str = match.group(0)
        json_str = json_str.replace("\\'", "'")
        json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
        data = json.loads(json_str)
    else:
        print("No JSON found")
        return None
   
    if "FINAL" in data.keys():
        return "llm_final : " + data['FINAL']


    results = await func_dict[data['TOOL_FUNC']](page, data['TOOL_ARGS'])
    if data['TOOL_FUNC'] == "ask_user":
        temp = "AI_ASKED" + str(data['TOOL_ARGS']) + "  USER_ RESPONDED : " + results
        await write_to_context(page=page, text=[temp])
    return results

func_dict = {"search_google":search_google,
             "get_google_page_links":get_google_page_links,
             "goto_link":goto_link,
             "search_website":search_website,
             "get_page_text":get_page_text,
             "write_to_context":write_to_context,
             "ask_user":ask_user,
             "get_ui_element":get_ui_element,
             "click_thing":click_thing,
             "fill_thing":fill_thing}

