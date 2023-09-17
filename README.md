# rentrylib
A python library for interfacing with the paste-site https://rentry.org

### Install

---
From PyPi: `python -m pip install rentrylib`</br>
From GitHub: `python -m pip install git+https://github.com/yntha/rentrylib`

### Usage

---
Create a new page with a custom URL and a custom edit code. Note that these are all optional parameters:
```py
page = rentrylib.RentryPage(
    text="Hello World! :)",
    custom_url='h3LLoW0RLd',
    edit_code='h*ll*w*rld'
)
```
---
Edit the page:
```py
response = page.edit({
    'text': 'Some new content.',
    'edit_code': "This shouldn't be used!",
    'new_edit_code': 'new password!!',
    'new_url': 'anewurl'
})
```
---
Delete this page:
```py
response = page.edit({'delete': True})

# or
response = page.delete()
```
---
Misc:
```py
# Get the page URL
# str
page_url = page.site

# Get the page `edit_code`
# str
edit_code = page.code

# Fetch the raw content of this page
# str
content = page.raw

# Fetch the content of this page as a PNG image.
# bytes
image = page.png

# Fetch the content of this page as a PDF document.
# bytes
document = page.pdf
```