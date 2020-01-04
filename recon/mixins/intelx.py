from time import sleep
from threading import RLock
from json import dumps
from copy import deepcopy
from urllib.parse import urljoin
from recon.core.framework import FrameworkException
from recon.mixins.threads import ThreadingMixin


class IntelXMixin(ThreadingMixin):
    # Cannot query faster than one request per second
    INTELX_COOLDOWN_SECONDS = 1.0

    def prepare_item(self, item):
        """
        Overwrite this function to prepare item for IntelX query
        :param item:
        :return: string representation of an item
        """
        return str(item)

    def save_results(self, intelx_response):
        """
        Overwrite this function to save IntelX responses to database.
        :param intelx_response: See IntelX API documentation.
        """
        raise FrameworkException(NotImplementedError())

    def search_routine(self, items, post_payload={}, get_payload={},
                       post_options={}, get_options={}):
        """
        Performs routine for intelligent search in sequential mode.
        :param items:
        :param post_payload: Payload used for POST request.
        :param get_payload: Payload used for GET request.
        :param post_options: Options used for POST request.
        :param get_options: Options used for GET request.
        """
        self.__routine(self.search_intelx_api,
                       self.search_result_intelx_api,
                       self.search_terminate_intelx_api,
                       post_payload,
                       get_payload,
                       post_options,
                       get_options,
                       items)

    def phonebook_routine(self, items, post_payload={}, get_payload={},
                          post_options={}, get_options={}):
        """
        Performs routine for phonebook search in sequential mode.
        :param items:
        :param post_payload: Payload used for POST request.
        :param get_payload: Payload used for GET request.
        :param post_options: Options used for POST request.
        :param get_options: Options used for GET request.
        """
        self.__routine(self.phonebook_intelx_api,
                       self.phonebook_result_intelx_api,
                       None,
                       post_payload,
                       get_payload,
                       post_options,
                       get_options,
                       items)

    def module_thread(self, item, post_func, get_func, term_func, post_payload,
                      get_payload, post_options, get_options, rest_api_lock,
                      db_lock):
        job_id = None
        try:
            i = self.prepare_item(item)
            post_payload["term"] = str(i)
            with rest_api_lock:
                response, data = post_func(payload=post_payload,
                                           options=post_options)
                sleep(self.INTELX_COOLDOWN_SECONDS)
            if response == 200:
                job_id = str(data["id"])
                get_payload["id"] = str(data["id"])
                with rest_api_lock:
                    data_response = get_func(get_payload, get_options)
                    sleep(self.INTELX_COOLDOWN_SECONDS)
                with db_lock:
                    self.save_results(data_response)
        except Exception as e:
            if term_func is not None and job_id is not None:
                self.error(
                    "Aborting search for {0!s} . Please do not interrupt."
                    .format(job_id))
                with rest_api_lock:
                    if term_func(job_id):
                        self.alert("Aborted: {0!s}".format(job_id))
                    sleep(self.INTELX_COOLDOWN_SECONDS)
            raise FrameworkException(e)

    def search_routine_threading(self, items, post_payload={}, get_payload={},
                                 post_options={}, get_options={}):
        """
        Performs routine for intelligent search in parallel mode.
        :param items:
        :param post_payload: Payload used for POST request.
        :param get_payload: Payload used for GET request.
        :param post_options: Options used for POST request.
        :param get_options: Options used for GET request.
        """
        self.__routine_threading(self.search_intelx_api,
                                 self.search_result_intelx_api,
                                 self.search_terminate_intelx_api,
                                 post_payload,
                                 get_payload,
                                 post_options,
                                 get_options,
                                 items)

    def phonebook_routine_threading(self, items, post_payload={},
                                    get_payload={}, post_options={},
                                    get_options={}):
        """
        Performs routine for phonebook search in parallel mode.
        :param items:
        :param post_payload: Payload used for POST request.
        :param get_payload: Payload used for GET request.
        :param post_options: Options used for POST request.
        :param get_options: Options used for GET request.
        """
        self.__routine_threading(self.phonebook_intelx_api,
                                 self.phonebook_result_intelx_api,
                                 None,
                                 post_payload,
                                 get_payload,
                                 post_options,
                                 get_options,
                                 items)

    def search_intelx_api(self, payload={}, options={}):
        """
        Performs a search request on intelligent endpoint
        :param payload: Dictionary overriding
        default payload parameters. See search_payload
        :param options:
        :return: response status code with UUID for executed search job
        """
        request_payload = deepcopy(self.search_payload)
        request_payload.update(payload)
        request_payload = self.__add_options_to_post_payload(payload, options)
        resp = self.__perform_post_query(self.endpoints["ix_search"],
                                         payload=request_payload)
        return self.__parse_search_request_response(resp)

    def search_result_intelx_api(self, payload={}, options={}):
        """
        Obtains results for specific intelligent search job
        :param payload: Dictionary overriding default payload parameters. See
        result_params
        :param options:
        :return: list of found results for specific job
        """
        result = []
        request_payload = deepcopy(self.result_params)
        request_payload.update(payload)
        if "limit" in options.keys():
            request_payload["limit"] = int(options["limit"])
        if "offset" in options.keys():
            request_payload["offset"] = int(options["offset"])
        if "previewlines" in options.keys():
            request_payload["previewlines"] = int(options["previewlines"])

        status = 3
        while status == 0 or status == 3:
            resp = self.__perform_get_query(self.endpoints["ix_search_result"],
                                            payload=request_payload)
            if resp.status_code in [204, 400, 401, 402, 404]:
                self.alert(self.responses[resp.status_code])
                break
            if resp.status_code == 200:
                data = resp.json()
                status = data["status"]

                if status == 2:
                    self.error("Search ID not found.")

                if status == 0 or status == 1:
                    result.extend(data["records"])
                sleep(self.INTELX_COOLDOWN_SECONDS)
        return result

    def search_terminate_intelx_api(self, uuid):
        """
        Terminates job on intelx server.
        :param uuid: Job ID
        :return: True if operation succeded.
        """
        request_payload = {"id": str(uuid)}
        resp = self.__perform_get_query(self.endpoints["ix_search_terminate"],
                                        payload=request_payload)
        return bool(resp.status_code == 200)

    def phonebook_intelx_api(self, payload={}, options={}):
        """
        Performs a search request on phonebook endpoint
        :param payload: Dictionary overriding
        default payload parameters. See search_payload
        :param options:
        :return: response status code with UUID for executed search job
        """
        request_payload = deepcopy(self.search_payload)
        request_payload.update(payload)
        request_payload = self.__add_options_to_post_payload(payload, options)
        resp = self.__perform_post_query(self.endpoints["ix_phonebook"],
                                         payload=request_payload)
        return self.__parse_search_request_response(resp)

    def phonebook_result_intelx_api(self, payload={}, options={}):
        """
        Obtains results for specific phonebook search job
        :param payload: Dictionary overriding default payload parameters. See
        result_params
        :param options:
        :return: list of selectors (dictionaries) with following keys:
        type, typeh (human readable), value, valueh (human readable)
        """
        result = []
        request_payload = deepcopy(self.result_params)
        request_payload.update(payload)
        if "offset" in options.keys():
            request_payload["offset"] = int(options["offset"])

        status = 3
        while status == 0 or status == 3:
            resp = self.__perform_get_query(
                self.endpoints["ix_phonebook_result"], payload=request_payload)
            if resp.status_code == 200:
                data = resp.json()
                status = data["status"]

                if status == 2:
                    self.error("Search ID not found.")

                if status == 0 or status == 1:
                    for selector in data["selectors"]:
                        result.append({
                            "type": selector["selectortype"],
                            "typeh": selector["selectortypeh"],
                            "value": selector["selectorvalue"],
                            "valueh": selector["selectorvalueh"]
                        })
        return result

    def __routine(self, post_func, get_func, term_func, post_payload,
                  get_payload, post_options, get_options, items):
        jobs_uuid = []
        try:
            for item in items:
                i = self.prepare_item(item)
                post_payload["term"] = str(i)
                response, data = post_func(payload=post_payload,
                                           options=post_options)
                if response == 200:
                    jobs_uuid.append(str(data["id"]))
                sleep(self.INTELX_COOLDOWN_SECONDS)
            while jobs_uuid:
                job_id = jobs_uuid[0]
                get_payload["id"] = str(job_id)
                data_response = get_func(get_payload, get_options)
                self.save_results(data_response)
                jobs_uuid.pop(0)
                sleep(self.INTELX_COOLDOWN_SECONDS)
        except Exception as e:
            self.error("Aborting all pending searches! "
                       "Please do not interrupt.")
            if term_func is not None:
                while jobs_uuid:
                    job_id = jobs_uuid[0]
                    if term_func(job_id):
                        jobs_uuid.pop(0)
                        self.alert("Aborted: {0!s}".format(job_id))
                        sleep(self.INTELX_COOLDOWN_SECONDS)
            raise FrameworkException(e)

    def __routine_threading(self, post_func, get_func, term_func, post_payload,
                            get_payload, post_options, get_options, items):
        rest_api_lock = RLock()
        db_lock = RLock()
        self.thread(items,
                    post_func,
                    get_func,
                    term_func,
                    post_payload,
                    get_payload,
                    post_options,
                    get_options,
                    rest_api_lock,
                    db_lock)

    def __perform_post_query(self, endpoint, payload={}):
        url, headers = self.__fetch_intelx_connection_info(endpoint)
        try:
            return self.request('POST', url, headers=headers,
                                data=dumps(payload))
        except Exception as e:
            raise FrameworkException(e)

    def __perform_get_query(self, endpoint, payload={}):
        url, headers = self.__fetch_intelx_connection_info(endpoint)
        try:
            return self.request('GET', url, headers=headers, params=payload)
        except Exception as e:
            raise FrameworkException(e)

    def __fetch_intelx_connection_info(self, endpoint):
        url = urljoin(str(self.get_key("intelx_domain")), endpoint)
        headers = {
            "user-agent": "ix-client/python",
            "x-key": str(self.get_key("intelx_api"))
        }
        return url, headers

    def __add_options_to_post_payload(self, payload={}, options={}):
        if "sort" in options.keys():
            payload["sort"] = int(self.sorting_dict[str(options["sort"])])

        # Date filters absence check operator is NOT-XOR
        # https://stackoverflow.com/questions/432842/how-do-you-get-the-logical-xor-of-two-variables-in-python
        if ("datefrom" in options.keys()) == ("dateto" in options.keys()):
            if ("datefrom" in options.keys()) and ("dateto" in options.keys()):
                payload["datefrom"] = str(options["datefrom"])
                payload["dateto"] = str(options["dateto"])
        else:
            self.error("If the date filters are used, both from and to date "
                       "must be supplied.")

        if "timeout" in options.keys():
            payload["timeout"] = int(options["timeout"])

        if "media" in options.keys():
            payload["media"] = \
                int({v: k for k, v in self.media_types}[options["media"]])

        if "buckets" in options.keys():
            payload["buckets"].extend(
                list(str(options["buckets"]).replace(" ", "").split(","))
            )

        if "maxresults" in options.keys():
            payload["maxresults"] = int(options["maxresults"])

        if "lookuplevel" in options.keys():
            payload["lookuplevel"] = int(options["lookuplevel"])
            self.alert("The lookuplevel field should always be 0.")

        return payload

    def __parse_search_request_response(self, response):
        if response.status_code in [204, 400, 401, 402, 404]:
            self.alert(self.responses[response.status_code])
            return response.status_code, None
        if response.status_code == 200:
            data = response.json()
            status = int(data["status"])
            if bool(data["softselectorwarning"]):
                self.alert("Soft selectors (generic terms) are not supported!")
            if status == 1:
                self.alert("Invalid term provided.")
            if status == 2:
                self.error("Error: Max concurrent searches per API key.")
            return response.status_code, str(data["id"])

    # Possible API endpoints
    endpoints = {
        "ix_search": "intelligent/search",
        "ix_search_result": "intelligent/search/result",
        "ix_search_terminate": "intelligent/search/terminate",
        "ix_phonebook": "phonebook/search",
        "ix_phonebook_result": "phonebook/search/result",
    }

    responses = {
        200: "OK.",
        204: "No content found.",
        400: "Invalid input. Please check whether the encoding is valid or all"
             " parameters are provided.",
        401: "Access not authorized due to probable missing permissions for "
             "API call or selected buckets.",
        402: "Payment Required. Authenticate: No credits available.",
        404: "Item or identifier not found."
    }

    # POST request default payload
    search_payload = {
        "term": "",
        "buckets": [],
        "lookuplevel": 0,
        "maxresults": 10,
        "timeout": 0,
        "datefrom": "",
        "dateto": "",
        "sort": 4,
        "media": 0,
        "terminate": []
    }

    # GET request default payload (results)
    result_params = {
        "id": "",
        "limit": 100
    }

    sorting_dict = {
        "": 0,                      # No sorting
        "least_relevant_first": 1,  # X-Score ASCENDING
        "most_relevant_first": 2,   # X-Score DESCENDING
        "oldest_first": 3,          # Date ASCENDING
        "newest_first": 4           # Date DESCENDING
    }

    # High-level
    media_types = {
        0: "",
        1: "paste_document",
        2: "paste_user",
        3: "forum",
        4: "forum_board",
        5: "forum_thread",
        6: "forum_post",
        7: "forum_user",
        8: "website_screenshot",
        9: "website_copy",
        13: "tweet",
        14: "url",
        15: "pdf",
        16: "doc",
        17: "xls",
        18: "ppt",
        19: "image",
        20: "audio",
        21: "video",
        22: "archive",
        23: "html",
        24: "txt"
    }

    # Low-level
    data_types = {
        0: "",
        1: "text",
        2: "image",
        3: "video",
        4: "audio",
        5: "document",
        6: "executable",
        7: "container",
        1001: "user",
        1002: "leak",
        1004: "url",
        1005: "forum"
    }
