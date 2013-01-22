    _/_/_/    _/_/_/_/    _/_/_/    _/_/_/    _/      _/            _/      _/    _/_/_/
   _/    _/  _/        _/        _/      _/  _/_/    _/            _/_/    _/  _/       
  _/_/_/    _/_/_/    _/        _/      _/  _/  _/  _/  _/_/_/_/  _/  _/  _/  _/  _/_/_/
 _/    _/  _/        _/        _/      _/  _/    _/_/            _/    _/_/  _/      _/ 
_/    _/  _/_/_/_/    _/_/_/    _/_/_/    _/      _/            _/      _/    _/_/_/    

Recon-ng is a full-featured Web Reconnaisance framework written in Python. Complete with independent modules, database interaction, built in convenience functions, interactive help, and command completion, Recon-ng provides a powerful environment in which open source web-based reconnaissance can be conducted quickly and thoroughly.

Recon-ng has a look and feel similar to the Metasploit Framework, reducing the learning curve for leveraging the framework. However, it is quite different. Recon-ng is not intended to compete with existing frameworks, as it is designed exclusively for web-based open source reconnaissance. If you want to exploit, use the Metasploit Framework. If you want to Social Engineer, us the Social Engineer Toolkit. If you want to conduct reconnaissance, use Recon-ng!

Recon-ng is a completely modular framework and makes it easy for even the newest of Python developers to contribute. Each module is a Subclass of the "module" class. The "module" class is a customized "cmd" interpreter equipped with built-in functionality that provides simple interfaces to common tasks such as standardizing output, interacting with the database, making web requests, and managing API keys. Therefore, all the hard work has been done for you. Building modules is simple and takes little more than a few minutes. While tasks, such as making web requests, can be done manually from within a module, there are benefits to using the prebuilt interfaces and convenience functions. For example, there are global settings to the framework which allow the user to specify a custom User-Agent string or enable proxying of requests. These global settings are only applied to requests made using the prebuilt interface.

Recon-ng comes packaged with many modules and is well equipped to begin supporting your reconnaissance efforts immediately. Here is some information about the included modules.

Auxiliary:
Auxiliary modules enhance the information that has already been stored in the database. The included modules look for known information leakage pages on hosts, conduct reverse lookups of hashed credentials, mangle names into usernames and email addresses, check whether or not an email address has been associated with a public credentials leak, and resolve hostnames to IP addresses.

Contacts:
Contacts modules harvest information about people that are associated with a given company and store it in the database. The included modules leverage LinkedIn and Jigsaw to harvest full names and job titles. The information gathered from the Contacts modules can be manipulated with the Auxiliary modules and used in conjunction with the Social Engineer Toolkit to produce devastating results. Recon-ng + SET, a match made in heaven.

Hosts:
Hosts modules harvest hosts that are associated with a given domain and store them in the database. The included modules leverage Baidu, Bing, Google, Shodan, and Yahoo search engines to enumerate internet aware hosts, and leverage DNS to brute guess hosts. The hosts gathered with the Hosts modules can assist penetration testers during the scoping process. They can also be used in conjunction with Auxiliary modules to identify known information leakage pages that contain active session IDs and authentication credentials.

Output:
Output modules create usable forms of the data stored in the database. The included modules provide the ability to create CSV and HTML reports. Whether you are looking to move data from Recon-ng to Excel, or create an appendix for a deliverable, we've got you covered.

Pwnedlist:
Recon-ng was not designed to deliver shell, but what if I told you that you could gain authenticated access to an environment without sending a packet to the target network or application? Pwnedlist modules leverage the Pwnedlist.com API to retrieve full credentials of "pwned" user accounts. The included modules retrieve single account credentials, credentials for all "pwned" accounts within a domain, or information about known leaks. Imagine having multiple sets of legitimate credentials for a VPN or web application prior to a penetration test even beginning. That's power that simply cannot be denied.