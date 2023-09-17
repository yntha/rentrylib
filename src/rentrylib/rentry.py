import ast
import os.path
import re
import requests
import urllib.parse

from http import HTTPStatus

RENTRY = "https://rentry.org"


class Rentry:
    def __init__(self):
        self.session = requests.session()

        # load the site cookies
        self.session.get(RENTRY)

    def exists(self, page_url: str):
        r_exists = self.get(f"{RENTRY}/{page_url}/exists")

        return bool(r_exists.text)

    def get_cookie(self, cookie_name: str) -> str:
        return self.session.cookies.get(cookie_name, default="")

    def get_token(self):
        return self.get_cookie("csrftoken")

    def get(self, page: str, *args, **kwargs) -> requests.Response:
        url = urllib.parse.urljoin(RENTRY, page)

        return self.session.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
                "Referer": url,
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
            },
            *args,
            **kwargs,
        )

    def post(self, page: str, *args, **kwargs) -> requests.Response:
        url = urllib.parse.urljoin(RENTRY, page)

        return self.session.post(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
                "Referer": url,
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
            },
            *args,
            **kwargs,
        )


class RentryPage:
    rentry = None

    def __init__(self, text: str = "", custom_url: str = "", edit_code: str = ""):
        self.code = edit_code
        self.site = custom_url

        if self.rentry is None:
            self.rentry = Rentry()

        # check if the page exists and if edit_code is valid
        if len(self.site) != 0 and self.rentry.exists(self.site):
            if len(self.code) != 0:
                r_edit = self.edit()

                if r_edit.status_code != HTTPStatus.FOUND:
                    raise Exception("Invalid edit code.")

        # create the site if it doesn't exist.
        else:
            r_create = self.rentry.post(
                "/",
                data={
                    "csrfmiddlewaretoken": self.rentry.get_token(),
                    "text": (text if len(text) > 0 else "."),
                    "edit_code": self.code,
                    "url": self.site,
                },
                allow_redirects=False,
            )

            if r_create.status_code != HTTPStatus.FOUND:
                raise Exception("Failed to create page.")

            ck_messages = ast.literal_eval(self.rentry.get_cookie("messages"))
            ck_messages = ck_messages.split(",")

            if len(ck_messages) <= 1 or "Your edit code: " not in ck_messages:
                raise Exception("Failed to get a `messages` cookie.")

            self.code = ck_messages[ck_messages.index("Your edit code: ") + 1]
            self.code = re.sub("[\\W_]+", "", self.code)
            self.site = urllib.parse.urlparse(r_create.headers["Location"])
            self.site = os.path.basename(self.site.path)

            # if this was created as an empty page, send a request to
            # delete the placeholder text.
            if len(text) == 0:
                self.edit({"text": ""})

    @property
    def raw(self) -> str:
        """
        Fetches and returns the raw markdown content of the page.

        :return: The raw page content.
        :rtype: str
        """
        r_raw = self.rentry.get(f"{self.site}/raw")

        if r_raw.status_code != HTTPStatus.OK:
            raise Exception("Failed to fetch raw text.")

        return r_raw.text

    @property
    def pdf(self) -> bytes:
        """
        Fetches and returns the page as a PDF document.

        :return: Bytes representing a page in PDF encoding
        :rtype: bytes
        """
        r_pdf = self.rentry.get(f"{self.site}/pdf")

        if r_pdf.status_code != HTTPStatus.OK:
            raise Exception("Failed to fetch pdf.")

        return r_pdf.content

    @property
    def png(self) -> bytes:
        """
        Fetches and returns the page as a PNG image.

        :return: Bytes representing a page in PNG encoding.
        """
        r_png = self.rentry.get(f"{self.site}/png")

        if r_png.status_code != HTTPStatus.OK:
            raise Exception("Failed to fetch png.")

        return r_png.content

    def edit(self, options: dict = None) -> requests.Response:
        """
        Edit a page. An `edit_code` is required to submit edits.

        :param dict options: A dictionary containing any of the following keys:
            - `text`: The page content. Uses the original content if not specified. Max
              200000 characters.
            - `edit_code`: The page's password. Required unless already given to class.
            - `new_edit_code`: New page password. Limited to 100 characters.
            - `new_url`: New custom URL for the page. Must contain only latin letters,
              numbers, underscores or hyphens.
            - `delete`: Set to `True` to delete this page. False by default.
        :return: HTTP Response. A status of 302 means success, any other is a failure.
        :rtype: requests.Response
        """
        if options is None:
            options = {}

        if options.get("new_edit_code") is not None:
            code = options["new_edit_code"]

            if len(code) == 0:
                raise Exception("New edit code must be >= 1 characters.")

        if options.get("new_url") is not None:
            url = options["new_url"]

            if len(url) < 2:
                raise Exception("Custom URL must have >= 2 characters.")
            if re.fullmatch("[A-Za-z0-9_-]", url) is None:
                raise Exception(
                    "Custom URL must contain only latin letters, numbers, underscores or hyphens."
                )
            if self.rentry.exists(url):
                raise Exception(f"Custom URL '{url}' already exists.")

        if self.code is None and options.get("edit_code") is None:
            raise Exception("No edit code provided.")

        r_edit = self.rentry.post(
            f"{self.site}/edit",
            data={
                "csrfmiddlewaretoken": self.rentry.get_token(),
                "text": options.get("text", self.raw),
                "edit_code": options.get("edit_code", self.code),
                "new_edit_code": options.get("new_edit_code", ""),
                "new_url": options.get("new_url", ""),
                "delete": ("delete" if options.get("delete", False) else ""),
            },
            allow_redirects=False,
        )

        return r_edit

    def delete(self, edit_code: str = None) -> requests.Response:
        """
        Delete this page.

        :param str edit_code: The page password.
        :return: HTTP Response
        :rtype: requests.Response
        """
        options = {"delete": True}

        if edit_code is not None:
            options["edit_code"] = edit_code

        r_delete = self.edit(options)

        if r_delete.status_code != HTTPStatus.FOUND:
            raise Exception("Failed to delete page.")

        return r_delete
