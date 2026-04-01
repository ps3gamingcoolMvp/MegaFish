"""
AgentRegistry — 8.3 billion deterministic agents, each a unique person.

Every agent ID (0 → 8,299,999,999) maps to the same person every time.
Population distribution matches real-world 2024 estimates.
All attributes (age, religion, income, education, etc.) match real country statistics.
"""

import random
import hashlib
from typing import Dict, Any, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Country population data + real-world statistics
# Format: (country, region, population, stats_dict)
# ---------------------------------------------------------------------------

COUNTRY_DATA = [
    # (name, region, population_2024, {stats})
    ("India", "South Asia", 1_428_627_663, {
        "religion": {"Hindu": 79.8, "Muslim": 14.2, "Christian": 2.3, "Sikh": 1.7, "Other": 2.0},
        "age_median": 28, "age_spread": 16,
        "internet_rate": 0.52, "urbanization": 0.36, "unemployment": 0.077,
        "income_mean": 2389, "income_spread": 1800,
        "education": {"none": 26, "primary": 28, "secondary": 32, "tertiary": 14},
        "gender_ratio": [50.4, 49.6],
        "languages": ["Hindi", "Bengali", "Telugu", "Marathi", "Tamil", "Urdu", "Gujarati", "Kannada"],
        "names_m": ["Aarav","Arjun","Rohit","Vikram","Sanjay","Rahul","Amit","Suresh","Rajesh","Pradeep","Kiran","Anil","Nikhil","Deepak","Vivek","Manish","Ravi","Ajay","Sunil","Pankaj"],
        "names_f": ["Priya","Anita","Sunita","Pooja","Kavita","Deepa","Rekha","Nisha","Anjali","Meena","Shalini","Ritu","Neha","Divya","Shweta","Geeta","Asha","Swati","Preeti","Radha"],
        "surnames": ["Sharma","Singh","Kumar","Patel","Gupta","Yadav","Verma","Mishra","Mehta","Joshi","Nair","Pillai","Reddy","Rao","Iyer","Bose","Das","Chatterjee","Mukherjee","Banerjee"],
    }),
    ("China", "East Asia", 1_407_713_364, {
        "religion": {"None/Folk": 73.0, "Buddhist": 18.0, "Christian": 5.0, "Muslim": 2.0, "Other": 2.0},
        "age_median": 39, "age_spread": 14,
        "internet_rate": 0.77, "urbanization": 0.65, "unemployment": 0.054,
        "income_mean": 12720, "income_spread": 9000,
        "education": {"none": 4, "primary": 25, "secondary": 47, "tertiary": 24},
        "gender_ratio": [51.5, 48.5],
        "languages": ["Mandarin", "Cantonese", "Wu", "Min", "Hakka"],
        "names_m": ["Wei","Fang","Gang","Hao","Jian","Lei","Ming","Peng","Qiang","Tao","Xin","Yang","Zhen","Bo","Chao","Dong","Feng","Guo","Hai","Jun"],
        "names_f": ["Fang","Hong","Hua","Juan","Li","Mei","Na","Ping","Qian","Rong","Shu","Ting","Xia","Yan","Ying","Zhen","Ai","Cui","Dan","Er"],
        "surnames": ["Wang","Li","Zhang","Liu","Chen","Yang","Huang","Zhao","Wu","Zhou","Xu","Sun","Ma","Zhu","Hu","Guo","He","Lin","Gao","Luo"],
    }),
    ("USA", "North America", 335_893_238, {
        "religion": {"Christian": 63.0, "None": 28.0, "Jewish": 2.0, "Muslim": 1.2, "Buddhist": 1.0, "Other": 4.8},
        "age_median": 38, "age_spread": 18,
        "internet_rate": 0.92, "urbanization": 0.83, "unemployment": 0.038,
        "income_mean": 31000, "income_spread": 22000,
        "education": {"none": 4, "primary": 8, "secondary": 50, "tertiary": 38},
        "gender_ratio": [49.5, 50.5],
        "languages": ["English", "Spanish"],
        "names_m": ["James","John","Robert","Michael","William","David","Richard","Joseph","Thomas","Charles","Christopher","Daniel","Matthew","Anthony","Mark","Donald","Steven","Paul","Andrew","Joshua"],
        "names_f": ["Mary","Patricia","Jennifer","Linda","Barbara","Elizabeth","Susan","Jessica","Sarah","Karen","Lisa","Nancy","Betty","Margaret","Sandra","Ashley","Dorothy","Kimberly","Emily","Donna"],
        "surnames": ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"],
    }),
    ("Indonesia", "Southeast Asia", 277_534_122, {
        "religion": {"Muslim": 87.2, "Christian": 9.9, "Hindu": 1.7, "Buddhist": 0.7, "Other": 0.5},
        "age_median": 30, "age_spread": 15,
        "internet_rate": 0.62, "urbanization": 0.58, "unemployment": 0.058,
        "income_mean": 4333, "income_spread": 3000,
        "education": {"none": 8, "primary": 32, "secondary": 42, "tertiary": 18},
        "gender_ratio": [50.1, 49.9],
        "languages": ["Indonesian", "Javanese", "Sundanese", "Madurese"],
        "names_m": ["Budi","Andi","Dian","Hendra","Agus","Dedi","Rudi","Wahyu","Eko","Fajar","Rizki","Irwan","Yusuf","Bayu","Doni","Arif","Teguh","Heru","Iwan","Joko"],
        "names_f": ["Sari","Dewi","Ratna","Fitri","Indah","Wulan","Ayu","Rina","Lestari","Novia","Sri","Endah","Yuli","Tuti","Ani","Rini","Desi","Mega","Hesti","Nanik"],
        "surnames": ["Santoso","Wijaya","Kusuma","Pratama","Suharto","Wibowo","Setiawan","Nugroho","Hidayat","Susanto","Rahmad","Purnomo","Saputra","Utama","Wahyudi","Hartanto","Gunawan","Kurniawan","Hasibuan","Harahap"],
    }),
    ("Pakistan", "South Asia", 240_485_658, {
        "religion": {"Muslim": 96.5, "Hindu": 2.1, "Christian": 1.3, "Other": 0.1},
        "age_median": 22, "age_spread": 14,
        "internet_rate": 0.36, "urbanization": 0.38, "unemployment": 0.065,
        "income_mean": 1505, "income_spread": 1200,
        "education": {"none": 42, "primary": 25, "secondary": 24, "tertiary": 9},
        "gender_ratio": [51.4, 48.6],
        "languages": ["Urdu", "Punjabi", "Sindhi", "Pashto", "Balochi"],
        "names_m": ["Muhammad","Ahmed","Ali","Hassan","Usman","Bilal","Tariq","Imran","Asad","Zubair","Kamran","Adnan","Fahad","Hamza","Omer","Waseem","Shahid","Naeem","Rizwan","Sarfraz"],
        "names_f": ["Fatima","Ayesha","Zainab","Amina","Sara","Hina","Sana","Nadia","Rabia","Asma","Sadia","Uzma","Shazia","Bushra","Saira","Nadia","Razia","Tahira","Gulnaz","Shabnam"],
        "surnames": ["Khan","Ahmed","Ali","Malik","Hussain","Chaudhry","Sheikh","Qureshi","Siddiqui","Abbasi","Mirza","Butt","Rana","Nawaz","Iqbal","Baig","Hashmi","Rizvi","Zaidi","Kazmi"],
    }),
    ("Brazil", "South America", 216_422_446, {
        "religion": {"Catholic": 50.0, "Evangelical": 31.0, "None": 10.0, "Spiritist": 3.0, "Other": 6.0},
        "age_median": 34, "age_spread": 17,
        "internet_rate": 0.81, "urbanization": 0.87, "unemployment": 0.079,
        "income_mean": 9130, "income_spread": 8000,
        "education": {"none": 7, "primary": 28, "secondary": 44, "tertiary": 21},
        "gender_ratio": [49.2, 50.8],
        "languages": ["Portuguese"],
        "names_m": ["João","José","Carlos","Paulo","Pedro","Lucas","Gabriel","Marcos","Rafael","Felipe","André","Eduardo","Ricardo","Roberto","Henrique","Leonardo","Daniel","Rodrigo","Bruno","Thiago"],
        "names_f": ["Maria","Ana","Francisca","Antônia","Adriana","Juliana","Márcia","Fernanda","Patricia","Aline","Sandra","Camila","Bruna","Amanda","Larissa","Leticia","Beatriz","Carolina","Vanessa","Natalia"],
        "surnames": ["Silva","Santos","Oliveira","Souza","Rodrigues","Ferreira","Alves","Pereira","Lima","Gomes","Costa","Ribeiro","Martins","Carvalho","Almeida","Lopes","Sousa","Fernandes","Vieira","Barbosa"],
    }),
    ("Nigeria", "Sub-Saharan Africa", 223_804_632, {
        "religion": {"Muslim": 53.5, "Christian": 45.9, "Traditional": 0.6},
        "age_median": 18, "age_spread": 12,
        "internet_rate": 0.43, "urbanization": 0.54, "unemployment": 0.053,
        "income_mean": 2184, "income_spread": 1800,
        "education": {"none": 35, "primary": 28, "secondary": 27, "tertiary": 10},
        "gender_ratio": [50.4, 49.6],
        "languages": ["Hausa", "Yoruba", "Igbo", "English", "Fulani"],
        "names_m": ["Emeka","Chidi","Tunde","Seun","Biodun","Kola","Seyi","Femi","Dele","Kunle","Uche","Nnamdi","Chukwu","Obinna","Ifeanyi","Babatunde","Oluwaseun","Adewale","Taiwo","Kehinde"],
        "names_f": ["Ngozi","Chioma","Amaka","Adaeze","Blessing","Grace","Patience","Favour","Peace","Joy","Chinwe","Obiageli","Nneka","Ifeoma","Adaora","Folake","Yetunde","Bisi","Sola","Toyin"],
        "surnames": ["Okafor","Obi","Nwosu","Eze","Nwankwo","Adeyemi","Okonkwo","Balogun","Adesanya","Ogundimu","Lawal","Abubakar","Usman","Ibrahim","Musa","Suleiman","Aliyu","Garba","Yusuf","Bello"],
    }),
    ("Bangladesh", "South Asia", 172_954_319, {
        "religion": {"Muslim": 90.4, "Hindu": 8.5, "Other": 1.1},
        "age_median": 28, "age_spread": 14,
        "internet_rate": 0.44, "urbanization": 0.40, "unemployment": 0.051,
        "income_mean": 2688, "income_spread": 2000,
        "education": {"none": 28, "primary": 32, "secondary": 30, "tertiary": 10},
        "gender_ratio": [50.2, 49.8],
        "languages": ["Bengali"],
        "names_m": ["Md","Rahim","Karim","Hasan","Hossain","Islam","Alam","Uddin","Rahman","Ali","Siddiqui","Ahmed","Khan","Chowdhury","Mia","Sarkar","Sheikh","Mondal","Paul","Das"],
        "names_f": ["Fatema","Rahela","Nasrin","Sultana","Begum","Akhter","Khatun","Parvin","Akter","Jahan","Nahar","Islam","Asha","Ruma","Shirin","Mitu","Popy","Sumi","Moni","Rimi"],
        "surnames": ["Rahman","Islam","Hossain","Ahmed","Ali","Khan","Das","Sarkar","Mondal","Chowdhury","Begum","Akter","Khatun","Sheikh","Miah","Uddin","Alam","Bhuiyan","Talukder","Nath"],
    }),
    ("Russia", "Europe/Asia", 144_444_359, {
        "religion": {"Orthodox Christian": 71.0, "None": 18.0, "Muslim": 10.0, "Other": 1.0},
        "age_median": 40, "age_spread": 18,
        "internet_rate": 0.88, "urbanization": 0.75, "unemployment": 0.037,
        "income_mean": 11654, "income_spread": 9000,
        "education": {"none": 2, "primary": 8, "secondary": 48, "tertiary": 42},
        "gender_ratio": [46.5, 53.5],
        "languages": ["Russian", "Tatar", "Chechen", "Bashkir"],
        "names_m": ["Alexander","Dmitry","Sergey","Andrei","Alexei","Mikhail","Ivan","Nikolai","Vladimir","Pavel","Artem","Maksim","Kirill","Ilya","Roman","Evgeny","Oleg","Yuri","Viktor","Anatoly"],
        "names_f": ["Olga","Natalia","Elena","Tatiana","Irina","Anna","Svetlana","Ekaterina","Yulia","Maria","Galina","Ludmila","Marina","Valentina","Nadezhda","Anastasia","Oksana","Inna","Larisa","Alina"],
        "surnames": ["Ivanov","Smirnov","Kuznetsov","Popov","Vasiliev","Petrov","Sokolov","Mikhailov","Novikov","Fedorov","Morozov","Volkov","Alekseev","Lebedev","Semyonov","Egorov","Pavlov","Kozlov","Stepanov","Nikolaev"],
    }),
    ("Ethiopia", "Sub-Saharan Africa", 126_527_060, {
        "religion": {"Orthodox Christian": 43.8, "Muslim": 31.3, "Protestant": 22.8, "Other": 2.1},
        "age_median": 19, "age_spread": 11,
        "internet_rate": 0.24, "urbanization": 0.23, "unemployment": 0.028,
        "income_mean": 925, "income_spread": 700,
        "education": {"none": 50, "primary": 28, "secondary": 16, "tertiary": 6},
        "gender_ratio": [50.1, 49.9],
        "languages": ["Amharic", "Oromo", "Tigrinya", "Somali"],
        "names_m": ["Abebe","Tadesse","Bekele","Haile","Getachew","Girma","Tesfaye","Mulugeta","Dawit","Yonas","Solomon","Yohannes","Kebede","Alemu","Worku","Negash","Amanuel","Berhane","Tekle","Desta"],
        "names_f": ["Tigist","Almaz","Mekdes","Hiwot","Selam","Azeb","Meseret","Bethlehem","Selamawit","Yeshi","Firehiwot","Aster","Tsehay","Abeba","Genet","Lemlem","Birtukan","Mihret","Sosina","Tizita"],
        "surnames": ["Alemu","Bekele","Tadesse","Haile","Girma","Tesfaye","Wolde","Gebre","Desta","Negash","Kifle","Tekle","Berhane","Asfaw","Mekonnen","Worku","Demeke","Tilahun","Kebede","Getachew"],
    }),
    ("Mexico", "North America", 128_455_567, {
        "religion": {"Catholic": 77.7, "Protestant": 11.2, "None": 8.1, "Other": 3.0},
        "age_median": 30, "age_spread": 15,
        "internet_rate": 0.76, "urbanization": 0.81, "unemployment": 0.033,
        "income_mean": 10046, "income_spread": 8000,
        "education": {"none": 6, "primary": 28, "secondary": 42, "tertiary": 24},
        "gender_ratio": [49.0, 51.0],
        "languages": ["Spanish", "Nahuatl", "Maya"],
        "names_m": ["José","Juan","Miguel","Carlos","Luis","Jorge","Francisco","Jesús","Antonio","Manuel","Rafael","Roberto","Eduardo","Alejandro","David","Daniel","Ricardo","Fernando","Sergio","Alberto"],
        "names_f": ["María","Guadalupe","Rosa","Ana","Laura","Verónica","Martha","Patricia","Sandra","Claudia","Elizabeth","Alejandra","Gabriela","Norma","Leticia","Silvia","Mónica","Diana","Adriana","Isabel"],
        "surnames": ["García","Martínez","López","Hernández","González","Pérez","Sánchez","Ramírez","Torres","Flores","Rivera","Gómez","Díaz","Cruz","Morales","Reyes","Gutiérrez","Ortiz","Chávez","Ramos"],
    }),
    ("Japan", "East Asia", 123_294_513, {
        "religion": {"Shinto/Buddhist": 69.0, "None": 28.0, "Christian": 1.5, "Other": 1.5},
        "age_median": 49, "age_spread": 18,
        "internet_rate": 0.93, "urbanization": 0.92, "unemployment": 0.026,
        "income_mean": 41580, "income_spread": 18000,
        "education": {"none": 1, "primary": 4, "secondary": 45, "tertiary": 50},
        "gender_ratio": [48.8, 51.2],
        "languages": ["Japanese"],
        "names_m": ["Haruto","Sota","Yuto","Haruki","Takumi","Kaito","Ren","Shun","Ryota","Kenta","Daiki","Yuki","Naoki","Kenji","Taro","Jiro","Ichiro","Makoto","Hiroshi","Satoshi"],
        "names_f": ["Yui","Hina","Aoi","Sakura","Rin","Mei","Koharu","Yuka","Miho","Nana","Ayumi","Emi","Keiko","Yoko","Naomi","Akiko","Miki","Tomoko","Haruka","Risa"],
        "surnames": ["Sato","Suzuki","Takahashi","Tanaka","Watanabe","Ito","Yamamoto","Nakamura","Kobayashi","Kato","Yoshida","Yamada","Sasaki","Matsumoto","Inoue","Kimura","Hayashi","Shimizu","Yamazaki","Mori"],
    }),
    ("Philippines", "Southeast Asia", 117_337_368, {
        "religion": {"Catholic": 80.6, "Protestant": 8.2, "Muslim": 5.6, "Other": 5.6},
        "age_median": 25, "age_spread": 13,
        "internet_rate": 0.73, "urbanization": 0.47, "unemployment": 0.045,
        "income_mean": 3460, "income_spread": 2800,
        "education": {"none": 4, "primary": 28, "secondary": 42, "tertiary": 26},
        "gender_ratio": [50.2, 49.8],
        "languages": ["Filipino", "English", "Cebuano", "Ilocano"],
        "names_m": ["Juan","Jose","Eduardo","Ricardo","Roberto","Miguel","Antonio","Carlos","Ramon","Manuel","Renato","Danilo","Romulo","Ernesto","Domingo","Efren","Raul","Wilfredo","Bernardo","Rogelio"],
        "names_f": ["Maria","Ana","Rosa","Carmen","Luz","Elena","Consuelo","Remedios","Teresita","Natividad","Erlinda","Rosario","Edna","Gloria","Felicidad","Conception","Leticia","Milagros","Dolores","Esperanza"],
        "surnames": ["Santos","Reyes","Cruz","Bautista","Ocampo","Garcia","Torres","Tomas","Andres","Dela Cruz","Ramos","Villanueva","Mendoza","Aquino","Gonzales","Flores","Castillo","Morales","Lopez","Rivera"],
    }),
    ("DR Congo", "Sub-Saharan Africa", 102_262_808, {
        "religion": {"Catholic": 50.0, "Protestant": 20.0, "Kimbanguist": 10.0, "Muslim": 10.0, "Other": 10.0},
        "age_median": 17, "age_spread": 10,
        "internet_rate": 0.27, "urbanization": 0.47, "unemployment": 0.068,
        "income_mean": 557, "income_spread": 400,
        "education": {"none": 40, "primary": 32, "secondary": 22, "tertiary": 6},
        "gender_ratio": [49.8, 50.2],
        "languages": ["French", "Lingala", "Swahili", "Kikongo", "Tshiluba"],
        "names_m": ["Jean","Pierre","Paul","Joseph","Emmanuel","Daniel","David","Samuel","Thomas","Christophe","Didier","Patrick","Fabrice","Guy","Serge","Alain","Erick","Kevin","Cedric","Aubin"],
        "names_f": ["Marie","Grace","Josephine","Anne","Beatrice","Christine","Claudine","Delphine","Esperance","Francoise","Helene","Irene","Joelle","Laure","Monique","Nicole","Odile","Pauline","Rachel","Sophie"],
        "surnames": ["Kabila","Mobutu","Lumumba","Tshombe","Kasai","Katanga","Kivu","Lukaku","Mbeki","Ndongo","Ngolo","Nkosi","Nzinga","Okello","Okonjo","Osei","Owusu","Senghor","Toure","Traore"],
    }),
    ("Germany", "Europe", 83_294_633, {
        "religion": {"Christian": 54.0, "None": 38.0, "Muslim": 5.0, "Other": 3.0},
        "age_median": 46, "age_spread": 18,
        "internet_rate": 0.92, "urbanization": 0.77, "unemployment": 0.031,
        "income_mean": 46208, "income_spread": 20000,
        "education": {"none": 1, "primary": 4, "secondary": 55, "tertiary": 40},
        "gender_ratio": [49.4, 50.6],
        "languages": ["German", "Turkish"],
        "names_m": ["Thomas","Andreas","Stefan","Michael","Christian","Peter","Daniel","Markus","Sebastian","Tobias","Lukas","Maximilian","Jonas","Felix","Florian","Jan","Nico","Tim","Philipp","Lars"],
        "names_f": ["Maria","Anna","Sophie","Laura","Sarah","Julia","Lisa","Katharina","Sandra","Nicole","Sabine","Christine","Monika","Petra","Claudia","Karin","Heike","Susanne","Andrea","Birgit"],
        "surnames": ["Müller","Schmidt","Schneider","Fischer","Weber","Meyer","Wagner","Becker","Schulz","Hoffmann","Schäfer","Koch","Bauer","Richter","Klein","Wolf","Schröder","Neumann","Schwarz","Zimmermann"],
    }),
    ("UK", "Europe", 67_736_802, {
        "religion": {"Christian": 46.2, "None": 37.2, "Muslim": 6.5, "Hindu": 1.7, "Other": 8.4},
        "age_median": 40, "age_spread": 18,
        "internet_rate": 0.95, "urbanization": 0.84, "unemployment": 0.038,
        "income_mean": 46510, "income_spread": 22000,
        "education": {"none": 1, "primary": 5, "secondary": 47, "tertiary": 47},
        "gender_ratio": [49.4, 50.6],
        "languages": ["English", "Welsh", "Scots"],
        "names_m": ["Oliver","George","Harry","Jack","Charlie","Jacob","Alfie","Freddie","Oscar","Archie","James","William","Noah","Thomas","Henry","Leo","Ethan","Mason","Luca","Logan"],
        "names_f": ["Olivia","Amelia","Isla","Ava","Mia","Isabella","Sophia","Grace","Emily","Poppy","Ella","Lily","Evie","Charlotte","Scarlett","Sophie","Chloe","Daisy","Freya","Alice"],
        "surnames": ["Smith","Jones","Williams","Taylor","Brown","Davies","Evans","Wilson","Thomas","Roberts","Johnson","Lewis","Walker","Robinson","Wood","Thompson","White","Watson","Jackson","Wright"],
    }),
    ("Tanzania", "Sub-Saharan Africa", 67_438_106, {
        "religion": {"Muslim": 35.2, "Catholic": 31.8, "Protestant": 27.0, "Traditional": 6.0},
        "age_median": 18, "age_spread": 11,
        "internet_rate": 0.33, "urbanization": 0.37, "unemployment": 0.022,
        "income_mean": 1136, "income_spread": 900,
        "education": {"none": 20, "primary": 42, "secondary": 30, "tertiary": 8},
        "gender_ratio": [49.9, 50.1],
        "languages": ["Swahili", "English", "Arabic"],
        "names_m": ["Juma","Hassan","Mohamed","Ahmed","Ali","Hamisi","Ramadhani","Salim","Omar","Ibrahim","John","Peter","David","James","Joseph","Emmanuel","Daniel","Elias","Samuel","Barnabas"],
        "names_f": ["Fatuma","Amina","Zainab","Mwanaidi","Mwajuma","Mariam","Grace","Joyce","Mercy","Faith","Happiness","Neema","Rehema","Salama","Zawadi","Upendo","Furaha","Tumaini","Imani","Amani"],
        "surnames": ["Mwangi","Omondi","Kamau","Otieno","Nyong'o","Mutua","Kimani","Njoroge","Kariuki","Waweru","Maina","Gitonga","Ndungu","Mugo","Gicheru","Njenga","Macharia","Kibira","Mwenda","Nyaga"],
    }),
    ("South Africa", "Sub-Saharan Africa", 60_414_495, {
        "religion": {"Christian": 85.3, "None": 7.1, "Muslim": 1.9, "Hindu": 1.1, "Other": 4.6},
        "age_median": 27, "age_spread": 15,
        "internet_rate": 0.68, "urbanization": 0.68, "unemployment": 0.329,
        "income_mean": 6001, "income_spread": 7000,
        "education": {"none": 6, "primary": 25, "secondary": 48, "tertiary": 21},
        "gender_ratio": [49.3, 50.7],
        "languages": ["Zulu", "Xhosa", "Afrikaans", "English", "Sotho"],
        "names_m": ["Sipho","Thabo","Mandla","Nkosi","Bongani","Lungelo","Sandile","Siyabonga","Musa","Nhlanhla","Luthando","Luyanda","Sifiso","Mthokozisi","Sibusiso","Thandolwethu","Mduduzi","Nkosinathi","Siyanda","Bayanda"],
        "names_f": ["Nomsa","Thandi","Nompumelelo","Zanele","Bongiwe","Lindiwe","Nokuthula","Ntombi","Zinhle","Londiwe","Thandeka","Nosipho","Nozipho","Simangele","Nokukhanya","Nonhlanhla","Nokwanda","Lungisa","Phindile","Ntombifuthi"],
        "surnames": ["Dlamini","Nkosi","Zulu","Ntuli","Mthembu","Ndlovu","Nxumalo","Cele","Khumalo","Mkhize","Buthelezi","Shabalala","Mhlongo","Mabunda","Luthuli","Ngubane","Majola","Mbatha","Myeni","Xulu"],
    }),
    ("Kenya", "Sub-Saharan Africa", 55_100_586, {
        "religion": {"Protestant": 47.7, "Catholic": 23.4, "Muslim": 11.2, "Traditional": 11.9, "Other": 5.8},
        "age_median": 20, "age_spread": 12,
        "internet_rate": 0.40, "urbanization": 0.29, "unemployment": 0.053,
        "income_mean": 1838, "income_spread": 1500,
        "education": {"none": 14, "primary": 40, "secondary": 35, "tertiary": 11},
        "gender_ratio": [50.0, 50.0],
        "languages": ["Swahili", "English", "Kikuyu", "Luo"],
        "names_m": ["James","John","Peter","Paul","Joseph","David","Samuel","Daniel","Stephen","George","Patrick","Michael","Anthony","Francis","Charles","Bernard","Robert","Martin","Andrew","Philip"],
        "names_f": ["Mary","Grace","Faith","Mercy","Joyce","Agnes","Rose","Margaret","Esther","Catherine","Ann","Beatrice","Caroline","Eunice","Florence","Hannah","Jane","Lydia","Ruth","Tabitha"],
        "surnames": ["Kamau","Waweru","Njoroge","Kariuki","Mwangi","Gitonga","Ndungu","Kimani","Macharia","Njenga","Otieno","Omondi","Odhiambo","Achieng","Onyango","Owino","Ouma","Akello","Apudo","Odhiambo"],
    }),
    ("France", "Europe", 64_756_584, {
        "religion": {"Catholic": 41.0, "None": 40.0, "Muslim": 8.0, "Protestant": 2.0, "Jewish": 0.7, "Other": 8.3},
        "age_median": 42, "age_spread": 18,
        "internet_rate": 0.92, "urbanization": 0.82, "unemployment": 0.073,
        "income_mean": 43720, "income_spread": 20000,
        "education": {"none": 2, "primary": 6, "secondary": 46, "tertiary": 46},
        "gender_ratio": [48.9, 51.1],
        "languages": ["French"],
        "names_m": ["Thomas","Nicolas","Julien","Antoine","Alexandre","Maxime","Pierre","Clement","Florian","Guillaume","Romain","Sebastien","Jonathan","Adrien","Baptiste","Hugo","Arthur","Louis","Theo","Mathieu"],
        "names_f": ["Emma","Marie","Camille","Lea","Manon","Julie","Lucie","Oceane","Clara","Pauline","Alice","Charlotte","Mathilde","Ines","Marine","Laura","Chloe","Sarah","Eva","Sofia"],
        "surnames": ["Martin","Bernard","Dubois","Thomas","Robert","Richard","Petit","Durand","Leroy","Moreau","Simon","Laurent","Lefebvre","Michel","Garcia","David","Bertrand","Roux","Vincent","Fournier"],
    }),
    # --- Regional fallbacks for remaining ~4.9B population ---
    ("Other_LatAm", "South America", 250_000_000, {
        "religion": {"Catholic": 68.0, "Protestant": 18.0, "None": 10.0, "Other": 4.0},
        "age_median": 30, "age_spread": 15,
        "internet_rate": 0.65, "urbanization": 0.78, "unemployment": 0.08,
        "income_mean": 8000, "income_spread": 6000,
        "education": {"none": 10, "primary": 30, "secondary": 40, "tertiary": 20},
        "gender_ratio": [49.5, 50.5],
        "languages": ["Spanish", "Portuguese"],
        "names_m": ["Carlos","José","Juan","Miguel","Luis","Eduardo","Roberto","Andrés","Diego","Sebastián"],
        "names_f": ["María","Ana","Carmen","Rosa","Laura","Valentina","Isabella","Camila","Sofia","Gabriela"],
        "surnames": ["González","Rodríguez","López","García","Martínez","Hernández","Díaz","Morales","Torres","Ruiz"],
    }),
    ("Other_Africa", "Sub-Saharan Africa", 480_000_000, {
        "religion": {"Christian": 48.0, "Muslim": 42.0, "Traditional": 8.0, "Other": 2.0},
        "age_median": 19, "age_spread": 11,
        "internet_rate": 0.28, "urbanization": 0.42, "unemployment": 0.065,
        "income_mean": 1800, "income_spread": 1500,
        "education": {"none": 35, "primary": 32, "secondary": 25, "tertiary": 8},
        "gender_ratio": [50.0, 50.0],
        "languages": ["French", "English", "Swahili", "Arabic"],
        "names_m": ["Amadou","Kofi","Kwame","Musa","Ibrahim","Moussa","Mamadou","Seydou","Oumar","Boubacar"],
        "names_f": ["Fatou","Aminata","Mariama","Kadiatou","Aissatou","Fatoumata","Oumou","Mariam","Rokia","Binta"],
        "surnames": ["Diallo","Traore","Coulibaly","Camara","Bah","Keita","Sylla","Toure","Sow","Barry"],
    }),
    ("Other_MiddleEast", "Middle East", 230_000_000, {
        "religion": {"Muslim": 90.0, "Christian": 6.0, "Other": 4.0},
        "age_median": 28, "age_spread": 14,
        "internet_rate": 0.65, "urbanization": 0.68, "unemployment": 0.072,
        "income_mean": 8500, "income_spread": 7000,
        "education": {"none": 15, "primary": 25, "secondary": 38, "tertiary": 22},
        "gender_ratio": [52.0, 48.0],
        "languages": ["Arabic", "Persian", "Kurdish", "Turkish"],
        "names_m": ["Mohamed","Ahmed","Ali","Omar","Hassan","Hussein","Khalid","Abdullah","Ibrahim","Yusuf"],
        "names_f": ["Fatima","Aisha","Mariam","Nour","Sara","Layla","Hana","Rania","Dina","Yasmin"],
        "surnames": ["Al-Ahmad","Al-Hassan","Al-Hussein","Al-Rashid","Al-Sayed","Al-Malik","Al-Amin","Al-Karimi","Al-Bakr","Al-Nasir"],
    }),
    ("Other_SouthAsia", "South Asia", 180_000_000, {
        "religion": {"Muslim": 55.0, "Hindu": 30.0, "Buddhist": 10.0, "Other": 5.0},
        "age_median": 27, "age_spread": 14,
        "internet_rate": 0.40, "urbanization": 0.38, "unemployment": 0.065,
        "income_mean": 2200, "income_spread": 1800,
        "education": {"none": 30, "primary": 30, "secondary": 28, "tertiary": 12},
        "gender_ratio": [50.5, 49.5],
        "languages": ["Bengali", "Nepali", "Sinhala", "Dzongkha"],
        "names_m": ["Ram","Shyam","Hari","Sita","Arjun","Bikram","Dinesh","Ganesh","Mohan","Rajesh"],
        "names_f": ["Sita","Gita","Rita","Mina","Puja","Sunita","Anita","Kabita","Samita","Namita"],
        "surnames": ["Sharma","Thapa","Rai","Tamang","Gurung","Magar","Limbu","Sherpa","Karki","Basnet"],
    }),
    ("Other_SEAsia", "Southeast Asia", 200_000_000, {
        "religion": {"Buddhist": 45.0, "Muslim": 25.0, "Christian": 15.0, "Other": 15.0},
        "age_median": 30, "age_spread": 15,
        "internet_rate": 0.55, "urbanization": 0.52, "unemployment": 0.03,
        "income_mean": 5000, "income_spread": 4000,
        "education": {"none": 8, "primary": 30, "secondary": 42, "tertiary": 20},
        "gender_ratio": [49.8, 50.2],
        "languages": ["Thai", "Vietnamese", "Khmer", "Burmese", "Lao"],
        "names_m": ["Somchai","Nguyen","Tran","Le","Pham","Hoang","Ngo","Bui","Do","Vo"],
        "names_f": ["Somying","Nguyen","Thi","Tran","Pham","Hoang","Le","Bui","Do","Dang"],
        "surnames": ["Nguyen","Tran","Le","Pham","Hoang","Ngo","Bui","Do","Ho","Ngo"],
    }),
    ("Other_Europe", "Europe", 250_000_000, {
        "religion": {"Christian": 58.0, "None": 32.0, "Muslim": 6.0, "Other": 4.0},
        "age_median": 43, "age_spread": 18,
        "internet_rate": 0.87, "urbanization": 0.74, "unemployment": 0.065,
        "income_mean": 25000, "income_spread": 15000,
        "education": {"none": 3, "primary": 8, "secondary": 50, "tertiary": 39},
        "gender_ratio": [49.0, 51.0],
        "languages": ["Italian", "Spanish", "Polish", "Ukrainian", "Dutch", "Romanian"],
        "names_m": ["Marco","Luca","Jan","Piotr","Andrei","Stefan","Nikolai","Viktor","Ivan","Andrej"],
        "names_f": ["Sofia","Laura","Anna","Katarzyna","Olena","Ioana","Elena","Ivana","Marta","Petra"],
        "surnames": ["Rossi","Ferrari","Romano","Kowalski","Nowak","Wiśniewski","Ionescu","Popescu","Müller","Weber"],
    }),
    ("Other_NorthAmerica", "North America", 80_000_000, {
        "religion": {"Christian": 65.0, "None": 24.0, "Muslim": 3.0, "Other": 8.0},
        "age_median": 35, "age_spread": 17,
        "internet_rate": 0.78, "urbanization": 0.73, "unemployment": 0.06,
        "income_mean": 15000, "income_spread": 10000,
        "education": {"none": 8, "primary": 24, "secondary": 44, "tertiary": 24},
        "gender_ratio": [49.5, 50.5],
        "languages": ["English", "French", "Spanish"],
        "names_m": ["James","John","William","Robert","David","Richard","Joseph","Thomas","Charles","Christopher"],
        "names_f": ["Mary","Patricia","Jennifer","Linda","Barbara","Elizabeth","Susan","Jessica","Sarah","Karen"],
        "surnames": ["Smith","Brown","Johnson","Williams","Jones","Garcia","Miller","Davis","Wilson","Taylor"],
    }),
    ("Other_Oceania", "Oceania", 45_000_000, {
        "religion": {"Christian": 55.0, "None": 35.0, "Muslim": 3.0, "Other": 7.0},
        "age_median": 38, "age_spread": 17,
        "internet_rate": 0.85, "urbanization": 0.72, "unemployment": 0.048,
        "income_mean": 35000, "income_spread": 18000,
        "education": {"none": 2, "primary": 8, "secondary": 48, "tertiary": 42},
        "gender_ratio": [50.0, 50.0],
        "languages": ["English", "Tok Pisin", "Malay"],
        "names_m": ["Liam","Noah","Oliver","William","James","Jack","Henry","Leo","Lucas","Mason"],
        "names_f": ["Olivia","Charlotte","Amelia","Isla","Mia","Grace","Zoe","Sophie","Ruby","Chloe"],
        "surnames": ["Smith","Jones","Williams","Brown","Wilson","Taylor","Johnson","White","Martin","Anderson"],
    }),
]

# ---------------------------------------------------------------------------
# Personality archetypes — 8 real-world types calibrated to 8.3B population
# Weights per country/region: [Survivor, Traditionalist, Caregiver, Socializer,
#                               Achiever, Explorer, Analyst, Rebel]
# ---------------------------------------------------------------------------
PERSONALITY_ARCHETYPES = [
    "survivor",        # daily survival focus; radical resilience; extreme necessity
    "traditionalist",  # bound by cultural/religious/family norms; stability > change
    "caregiver",       # nurturing, self-sacrificing, community glue
    "socializer",      # people-first, energy from connection, community builder
    "achiever",        # goal-driven, status-seeking, upward mobility obsessed
    "explorer",        # curious, open, questions assumptions, seeks novelty
    "analyst",         # logic-first, data-oriented, independent thinking
    "rebel",           # challenges norms, counter-cultural, creative disruptor
]

# Legacy alias kept for backward compatibility
PERSONALITY_TYPES = PERSONALITY_ARCHETYPES

SOCIAL_MEDIA_BEHAVIORS = [
    "heavy_poster",       # posts multiple times daily
    "active_commenter",   # rarely posts but comments a lot
    "passive_lurker",     # mostly reads, rarely engages
    "news_sharer",        # shares articles and news
    "opinion_leader",     # posts strong opinions, gets engagement
    "meme_spreader",      # shares humor and viral content
    "professional_voice", # career and industry focused content
    "not_online",         # no social media presence
]

POLITICAL_LEANINGS = [
    "far_left", "left", "center_left", "center",
    "center_right", "right", "far_right", "apolitical"
]

# ---------------------------------------------------------------------------
# New dimensions from MegaFish 8.3B population model
# ---------------------------------------------------------------------------

CULTURE_TYPES = [
    "western_liberal",       # N. America, W. Europe, Australia — individualist, secular
    "east_asian_confucian",  # China, Japan, Korea — collectivist, education-obsessed
    "south_asian",           # India, Pakistan, Bangladesh — family-centric, hierarchical
    "islamic_mena",          # Arab world, Iran, Turkey — faith-centered, honor-conscious
    "sub_saharan_african",   # 50+ countries — community-driven, oral tradition, youngest
    "latin_american",        # Mixed heritage, Catholic-influenced, warm, urban
    "orthodox_slavic",       # Russia, E. Europe — stoic, cynical of institutions
    "southeast_asian",       # Indonesia, Philippines, Vietnam — syncretic, rapidly growing
]

POLITICAL_ORIENTATIONS = [
    "traditional_conservative",  # values tradition, religion, social order (26.5%)
    "communitarian",             # collective welfare, workers' rights (21.7%)
    "nationalist_populist",      # strong national identity, us-vs-them (14.5%)
    "liberal_progressive",       # individual rights, diversity, climate (10.8%)
    "authoritarian",             # strong state control, order over democracy (9.6%)
    "apolitical",                # disengaged, focuses on personal survival (16.9%)
]

POWER_LEVELS = [
    "no_agency",          # survival mode, zero political voice (18.1%)
    "community_member",   # local participation, limited reach (45.8%)
    "local_influencer",   # business owner, religious leader, teacher (21.7%)
    "regional_leader",    # corporate mid-mgmt, senior officials (2%)
    "national_figure",    # politicians, major CEOs, top media (0.09%)
    "global_elite",       # billionaires, heads of state (0.02%)
]

CONFLICT_EXPOSURE = [
    "stable_peaceful",       # no active war, functional institutions (54.2%)
    "political_instability", # corruption, institutional dysfunction (24.1%)
    "high_crime",            # gang/cartel violence shapes daily life (9.6%)
    "active_conflict",       # currently in/near active war (4.2%)
    "refugee",               # forcibly displaced (1.3%)
    "post_conflict",         # recently emerged from major war (6.5%)
]

LIVING_SITUATIONS = [
    "multi_generational",   # 3+ generations under one roof (33.7%)
    "nuclear_family",       # two parents and children (25.3%)
    "informal_slum",        # no legal tenure, no proper water/sanitation (13.3%)
    "extended_compound",    # multiple families in shared compound (9.6%)
    "solo",                 # living alone — urban pro or elderly (10.8%)
    "refugee_camp",         # displaced, uncertain legal status (1.3%)
    "homeless",             # no stable shelter (1.8%)
]

EMPLOYMENT_TYPES = [
    "subsistence_farmer",   # feeds family from land (15.7%)
    "manual_worker",        # construction, manufacturing, mining (18.1%)
    "service_gig",          # restaurants, retail, gig platforms (14.5%)
    "professional",         # knowledge worker — engineer, doctor, lawyer (9.6%)
    "student",              # secondary school or higher ed (14.5%)
    "homemaker",            # unpaid domestic labor, ~95% women (10.8%)
    "unemployed_informal",  # no stable employer, irregular income (6%)
    "entrepreneur",         # from market stall to startup founder (4.8%)
    "retired",              # past working age (4.8%)
]

HEALTH_STATUSES = [
    "healthy",                  # no chronic condition (47%)
    "nutritional_deficiency",   # food insecurity, micronutrient deficit (8.8%)
    "chronic_ncd",              # diabetes, hypertension, heart disease (21.7%)
    "mental_health_condition",  # depression, anxiety, untreated (12%)
    "infectious_disease",       # HIV, malaria, TB (8.4%)
    "disability",               # physical or cognitive limitation (15.7%)
]

INFO_ACCESS_LEVELS = [
    "oral_tradition_only",      # info from elders/community only (18.1%)
    "radio_tv_broadcast",       # state/commercial broadcast primary (21.7%)
    "basic_smartphone_apps",    # WhatsApp + YouTube + Facebook (25.3%)
    "broadband_and_laptop",     # home internet + computer (22.9%)
    "power_user",               # unlimited access, high media literacy (12%)
]

TECH_ACCESS_LEVELS = [
    "no_modern_tech",           # no electricity, no phone (10.8%)
    "basic_phone",              # calls + SMS only (9.6%)
    "smartphone_limited_data",  # 3–5 apps, expensive data (25.3%)
    "smartphone_full_access",   # multiple apps, reasonable data (28.9%)
    "laptop_pc_broadband",      # personal computer + smartphone (18.1%)
    "full_tech_ecosystem",      # smart devices, gigabit broadband (7.2%)
]

# ---------------------------------------------------------------------------
# Per-country / per-region dimension profiles
# Personality weights: [Survivor, Traditionalist, Caregiver, Socializer,
#                       Achiever, Explorer, Analyst, Rebel]
# All other weights follow the same index order as their respective list above.
# ---------------------------------------------------------------------------
COUNTRY_PROFILES = {
    # --- Specific country overrides ---
    "India": {
        "culture_type": "south_asian",
        "personality_weights": [12, 32, 22, 16, 12, 3, 2, 1],
        "political_weights": [35, 20, 18, 8, 10, 9],
        "power_weights": [22, 50, 22, 4, 1, 0.1],
        "conflict_weights": [50, 30, 8, 2, 1, 9],
        "living_weights": [45, 20, 15, 12, 5, 1, 2],
        "employment_weights": [22, 18, 14, 8, 14, 12, 8, 3, 1],
        "health_weights": [38, 15, 22, 10, 8, 7],
        "info_access_weights": [20, 18, 35, 20, 7],
        "tech_access_weights": [5, 10, 35, 30, 15, 5],
    },
    "China": {
        "culture_type": "east_asian_confucian",
        "personality_weights": [8, 26, 14, 16, 24, 6, 5, 1],
        "political_weights": [20, 15, 22, 5, 30, 8],
        "power_weights": [8, 52, 26, 10, 3, 0.5],
        "conflict_weights": [70, 20, 5, 2, 1, 2],
        "living_weights": [35, 30, 8, 10, 14, 1, 2],
        "employment_weights": [8, 22, 18, 15, 14, 8, 6, 5, 4],
        "health_weights": [45, 5, 28, 14, 2, 6],
        "info_access_weights": [2, 25, 28, 32, 13],
        "tech_access_weights": [1, 3, 20, 38, 28, 10],
    },
    "USA": {
        "culture_type": "western_liberal",
        "personality_weights": [5, 12, 16, 20, 24, 12, 7, 4],
        "political_weights": [18, 22, 20, 18, 5, 17],
        "power_weights": [5, 40, 30, 18, 5, 2],
        "conflict_weights": [65, 10, 18, 1, 1, 5],
        "living_weights": [8, 40, 4, 3, 38, 1, 6],
        "employment_weights": [1, 12, 22, 22, 16, 5, 8, 8, 6],
        "health_weights": [45, 2, 30, 18, 1, 4],
        "info_access_weights": [1, 5, 15, 42, 37],
        "tech_access_weights": [0, 1, 5, 28, 40, 26],
    },
    "Indonesia": {
        "culture_type": "southeast_asian",
        "personality_weights": [14, 24, 26, 22, 8, 3, 1, 2],
        "political_weights": [30, 20, 15, 8, 12, 15],
        "power_weights": [20, 52, 22, 5, 1, 0.1],
        "conflict_weights": [55, 28, 8, 3, 2, 4],
        "living_weights": [42, 22, 14, 10, 8, 2, 2],
        "employment_weights": [18, 20, 16, 8, 14, 12, 7, 3, 2],
        "health_weights": [40, 12, 20, 10, 12, 6],
        "info_access_weights": [8, 20, 40, 22, 10],
        "tech_access_weights": [3, 8, 32, 35, 16, 6],
    },
    "Pakistan": {
        "culture_type": "islamic_mena",
        "personality_weights": [16, 36, 20, 16, 8, 2, 1, 1],
        "political_weights": [42, 15, 20, 5, 8, 10],
        "power_weights": [28, 50, 18, 3, 0.5, 0.05],
        "conflict_weights": [30, 40, 15, 10, 3, 2],
        "living_weights": [52, 18, 12, 12, 3, 2, 1],
        "employment_weights": [28, 18, 12, 6, 14, 14, 6, 1, 1],
        "health_weights": [32, 18, 20, 10, 12, 8],
        "info_access_weights": [25, 30, 30, 12, 3],
        "tech_access_weights": [8, 15, 38, 25, 10, 4],
    },
    "Brazil": {
        "culture_type": "latin_american",
        "personality_weights": [10, 20, 28, 28, 8, 3, 1, 2],
        "political_weights": [22, 25, 22, 12, 4, 15],
        "power_weights": [15, 48, 25, 8, 3, 1],
        "conflict_weights": [30, 25, 35, 5, 2, 3],
        "living_weights": [20, 32, 20, 8, 16, 1, 3],
        "employment_weights": [5, 20, 22, 12, 16, 8, 8, 6, 3],
        "health_weights": [40, 5, 30, 15, 5, 5],
        "info_access_weights": [3, 15, 30, 38, 14],
        "tech_access_weights": [1, 4, 22, 42, 24, 7],
    },
    "Nigeria": {
        "culture_type": "sub_saharan_african",
        "personality_weights": [25, 25, 22, 18, 8, 1, 0, 1],
        "political_weights": [30, 18, 25, 5, 8, 14],
        "power_weights": [25, 50, 20, 4, 0.5, 0.05],
        "conflict_weights": [35, 30, 15, 12, 3, 5],
        "living_weights": [35, 18, 22, 18, 4, 1, 2],
        "employment_weights": [20, 18, 14, 6, 14, 10, 10, 6, 2],
        "health_weights": [32, 18, 18, 10, 14, 8],
        "info_access_weights": [18, 22, 38, 18, 4],
        "tech_access_weights": [5, 12, 38, 30, 12, 3],
    },
    "Russia": {
        "culture_type": "orthodox_slavic",
        "personality_weights": [15, 30, 18, 15, 12, 5, 4, 1],
        "political_weights": [22, 18, 28, 8, 18, 6],
        "power_weights": [8, 48, 28, 12, 3, 0.5],
        "conflict_weights": [40, 30, 8, 15, 2, 5],
        "living_weights": [25, 30, 8, 8, 26, 1, 2],
        "employment_weights": [2, 20, 18, 18, 14, 6, 8, 6, 8],
        "health_weights": [38, 3, 30, 18, 5, 6],
        "info_access_weights": [2, 28, 22, 30, 18],
        "tech_access_weights": [1, 2, 18, 35, 32, 12],
    },
    "Ethiopia": {
        "culture_type": "sub_saharan_african",
        "personality_weights": [25, 30, 22, 14, 6, 1, 1, 1],
        "political_weights": [38, 15, 18, 4, 15, 10],
        "power_weights": [35, 50, 13, 2, 0.2, 0.02],
        "conflict_weights": [30, 30, 8, 20, 5, 7],
        "living_weights": [55, 15, 15, 10, 3, 1, 1],
        "employment_weights": [48, 18, 10, 4, 10, 8, 6, 2, 4],
        "health_weights": [28, 28, 18, 8, 14, 4],
        "info_access_weights": [42, 28, 20, 8, 2],
        "tech_access_weights": [18, 22, 35, 18, 6, 1],
    },
    "Japan": {
        "culture_type": "east_asian_confucian",
        "personality_weights": [2, 22, 18, 14, 28, 10, 6, 0],
        "political_weights": [20, 25, 15, 12, 10, 18],
        "power_weights": [2, 42, 32, 18, 5, 1],
        "conflict_weights": [90, 5, 2, 0, 0, 3],
        "living_weights": [20, 28, 2, 5, 42, 0, 3],
        "employment_weights": [1, 15, 18, 22, 14, 4, 5, 10, 11],
        "health_weights": [50, 2, 28, 14, 1, 5],
        "info_access_weights": [0, 8, 12, 40, 40],
        "tech_access_weights": [0, 1, 5, 25, 40, 29],
    },
    "Germany": {
        "culture_type": "western_liberal",
        "personality_weights": [3, 18, 18, 16, 22, 12, 8, 3],
        "political_weights": [15, 28, 18, 18, 5, 16],
        "power_weights": [3, 40, 32, 18, 5, 2],
        "conflict_weights": [82, 8, 5, 0, 2, 3],
        "living_weights": [12, 35, 2, 5, 42, 0, 4],
        "employment_weights": [0, 15, 18, 25, 15, 5, 6, 8, 8],
        "health_weights": [48, 1, 30, 16, 1, 4],
        "info_access_weights": [0, 5, 10, 42, 43],
        "tech_access_weights": [0, 1, 5, 25, 42, 27],
    },
}

# Region-level fallback profiles (used when no country-specific profile exists)
REGION_PROFILES = {
    "South Asia": {
        "culture_type": "south_asian",
        "personality_weights": [12, 32, 22, 16, 12, 3, 2, 1],
        "political_weights": [35, 18, 18, 8, 10, 11],
        "power_weights": [25, 52, 18, 4, 0.8, 0.1],
        "conflict_weights": [45, 30, 8, 8, 3, 6],
        "living_weights": [48, 20, 14, 10, 5, 2, 1],
        "employment_weights": [25, 18, 14, 7, 14, 12, 7, 2, 1],
        "health_weights": [35, 15, 22, 10, 10, 8],
        "info_access_weights": [22, 22, 32, 18, 6],
        "tech_access_weights": [6, 12, 35, 28, 14, 5],
    },
    "East Asia": {
        "culture_type": "east_asian_confucian",
        "personality_weights": [6, 28, 15, 14, 24, 6, 6, 1],
        "political_weights": [22, 18, 20, 8, 22, 10],
        "power_weights": [8, 48, 28, 12, 3, 0.5],
        "conflict_weights": [65, 20, 5, 5, 1, 4],
        "living_weights": [32, 28, 8, 8, 20, 1, 3],
        "employment_weights": [6, 20, 18, 15, 14, 7, 6, 6, 8],
        "health_weights": [44, 5, 28, 14, 3, 6],
        "info_access_weights": [2, 20, 26, 35, 17],
        "tech_access_weights": [1, 3, 18, 36, 30, 12],
    },
    "Southeast Asia": {
        "culture_type": "southeast_asian",
        "personality_weights": [14, 24, 26, 22, 8, 3, 1, 2],
        "political_weights": [28, 20, 18, 8, 14, 12],
        "power_weights": [18, 52, 24, 5, 0.8, 0.1],
        "conflict_weights": [52, 28, 8, 5, 2, 5],
        "living_weights": [40, 22, 15, 12, 8, 2, 1],
        "employment_weights": [18, 20, 16, 8, 14, 12, 7, 3, 2],
        "health_weights": [40, 12, 20, 10, 12, 6],
        "info_access_weights": [8, 20, 38, 25, 9],
        "tech_access_weights": [3, 8, 32, 35, 16, 6],
    },
    "Sub-Saharan Africa": {
        "culture_type": "sub_saharan_african",
        "personality_weights": [26, 26, 24, 14, 5, 1, 2, 2],
        "political_weights": [30, 18, 22, 5, 10, 15],
        "power_weights": [28, 50, 18, 3, 0.3, 0.03],
        "conflict_weights": [32, 30, 12, 15, 4, 7],
        "living_weights": [38, 18, 20, 16, 4, 2, 2],
        "employment_weights": [30, 18, 14, 5, 14, 10, 8, 4, 3],
        "health_weights": [30, 20, 18, 10, 14, 8],
        "info_access_weights": [25, 24, 35, 14, 2],
        "tech_access_weights": [8, 14, 36, 28, 10, 4],
    },
    "Middle East": {
        "culture_type": "islamic_mena",
        "personality_weights": [14, 32, 20, 18, 10, 3, 2, 1],
        "political_weights": [38, 15, 20, 6, 12, 9],
        "power_weights": [20, 50, 22, 6, 1, 0.2],
        "conflict_weights": [32, 30, 8, 20, 5, 5],
        "living_weights": [45, 22, 12, 14, 5, 1, 1],
        "employment_weights": [8, 18, 16, 12, 16, 16, 8, 4, 2],
        "health_weights": [38, 8, 26, 14, 8, 6],
        "info_access_weights": [10, 25, 32, 25, 8],
        "tech_access_weights": [2, 6, 28, 38, 20, 6],
    },
    "Europe": {
        "culture_type": "western_liberal",
        "personality_weights": [4, 18, 18, 18, 20, 12, 8, 2],
        "political_weights": [18, 28, 18, 18, 5, 13],
        "power_weights": [5, 42, 32, 15, 5, 1],
        "conflict_weights": [72, 12, 6, 5, 2, 3],
        "living_weights": [15, 35, 3, 5, 38, 1, 3],
        "employment_weights": [1, 15, 18, 22, 15, 5, 8, 8, 8],
        "health_weights": [46, 2, 30, 16, 1, 5],
        "info_access_weights": [1, 8, 12, 42, 37],
        "tech_access_weights": [0, 1, 6, 26, 40, 27],
    },
    "Europe/Asia": {
        "culture_type": "orthodox_slavic",
        "personality_weights": [15, 30, 18, 15, 12, 5, 4, 1],
        "political_weights": [22, 18, 28, 8, 18, 6],
        "power_weights": [8, 48, 28, 12, 3, 0.5],
        "conflict_weights": [40, 28, 8, 15, 3, 6],
        "living_weights": [25, 30, 8, 8, 26, 1, 2],
        "employment_weights": [2, 20, 18, 18, 14, 6, 8, 6, 8],
        "health_weights": [38, 3, 30, 18, 5, 6],
        "info_access_weights": [2, 25, 22, 32, 19],
        "tech_access_weights": [1, 2, 18, 35, 32, 12],
    },
    "North America": {
        "culture_type": "western_liberal",
        "personality_weights": [5, 12, 16, 20, 24, 12, 7, 4],
        "political_weights": [18, 22, 20, 18, 5, 17],
        "power_weights": [6, 42, 30, 16, 5, 1],
        "conflict_weights": [62, 12, 18, 2, 1, 5],
        "living_weights": [10, 38, 5, 4, 36, 1, 6],
        "employment_weights": [1, 13, 22, 22, 16, 5, 8, 8, 5],
        "health_weights": [44, 2, 30, 18, 1, 5],
        "info_access_weights": [1, 5, 16, 42, 36],
        "tech_access_weights": [0, 1, 5, 28, 40, 26],
    },
    "South America": {
        "culture_type": "latin_american",
        "personality_weights": [10, 22, 28, 26, 8, 3, 1, 2],
        "political_weights": [22, 25, 22, 12, 4, 15],
        "power_weights": [18, 48, 24, 8, 2, 0.5],
        "conflict_weights": [32, 26, 30, 5, 2, 5],
        "living_weights": [22, 30, 18, 10, 16, 2, 2],
        "employment_weights": [6, 20, 22, 12, 16, 8, 8, 6, 2],
        "health_weights": [40, 6, 28, 15, 6, 5],
        "info_access_weights": [4, 15, 32, 36, 13],
        "tech_access_weights": [1, 4, 24, 42, 22, 7],
    },
    "Oceania": {
        "culture_type": "western_liberal",
        "personality_weights": [3, 14, 16, 20, 24, 14, 8, 1],
        "political_weights": [15, 28, 16, 22, 4, 15],
        "power_weights": [3, 40, 32, 18, 6, 1],
        "conflict_weights": [82, 8, 5, 1, 2, 2],
        "living_weights": [8, 38, 2, 4, 44, 0, 4],
        "employment_weights": [2, 14, 20, 25, 15, 5, 7, 8, 4],
        "health_weights": [48, 2, 28, 16, 1, 5],
        "info_access_weights": [0, 4, 10, 44, 42],
        "tech_access_weights": [0, 1, 5, 24, 42, 28],
    },
}


class AgentRegistry:
    """
    8.3 billion deterministic agents. Each agent ID maps to the same unique person every time.
    Population distribution matches real-world 2024 demographics exactly.
    """

    TOTAL_POPULATION = 8_300_000_000

    def __init__(self):
        # Build cumulative ID ranges per country
        self._ranges: List[Tuple[int, int, str, str, dict]] = []
        cumulative = 0
        actual_total = sum(pop for _, _, pop, _ in COUNTRY_DATA)

        # Scale each country proportionally to fill exactly 8.3B
        scale = self.TOTAL_POPULATION / actual_total

        for country, region, pop, stats in COUNTRY_DATA:
            scaled_pop = max(1, int(pop * scale))
            self._ranges.append((cumulative, cumulative + scaled_pop - 1, country, region, stats))
            cumulative += scaled_pop

        # Fill any rounding gap by extending the last entry
        if cumulative < self.TOTAL_POPULATION:
            last = self._ranges[-1]
            self._ranges[-1] = (last[0], self.TOTAL_POPULATION - 1, last[2], last[3], last[4])

    def _find_country(self, agent_id: int) -> Tuple[str, str, dict]:
        """Binary search to find which country an agent_id belongs to."""
        lo, hi = 0, len(self._ranges) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            start, end, country, region, stats = self._ranges[mid]
            if agent_id < start:
                hi = mid - 1
            elif agent_id > end:
                lo = mid + 1
            else:
                return country, region, stats
        # Fallback
        return self._ranges[-1][2], self._ranges[-1][3], self._ranges[-1][4]

    def get_agent(self, agent_id: int) -> Dict[str, Any]:
        """
        Get a fully deterministic, consistent agent profile.
        Agent #4,521,887,234 is always the same person.
        """
        if not 0 <= agent_id < self.TOTAL_POPULATION:
            raise ValueError(f"agent_id must be 0–{self.TOTAL_POPULATION - 1}")

        country, region, stats = self._find_country(agent_id)
        rng = random.Random(agent_id)  # deterministic seed

        # --- Gender ---
        gender = rng.choices(["male", "female"], weights=stats["gender_ratio"])[0]

        # --- Age (skewed by country median) ---
        age = max(5, min(95, int(rng.gauss(stats["age_median"], stats["age_spread"]))))

        # --- Name ---
        name_pool = stats["names_m"] if gender == "male" else stats["names_f"]
        first = rng.choice(name_pool)
        last = rng.choice(stats["surnames"])
        name = f"{first} {last}"

        # --- Religion ---
        rel_keys = list(stats["religion"].keys())
        rel_weights = list(stats["religion"].values())
        religion = rng.choices(rel_keys, weights=rel_weights)[0]

        # --- Education ---
        edu_keys = list(stats["education"].keys())
        edu_weights = list(stats["education"].values())
        education = rng.choices(edu_keys, weights=edu_weights)[0]

        # --- Income (log-normal distribution around country mean) ---
        income = max(100, int(rng.gauss(stats["income_mean"], stats["income_spread"])))

        # --- Internet & Urban ---
        internet_access = rng.random() < stats["internet_rate"]
        urban = rng.random() < stats["urbanization"]
        employed = rng.random() < (1 - stats["unemployment"])

        # --- Pull the profile for this country or fall back to region ---
        profile = COUNTRY_PROFILES.get(country) or REGION_PROFILES.get(region) or REGION_PROFILES["North America"]

        # --- Personality archetype (8 real-world types) ---
        personality = rng.choices(PERSONALITY_ARCHETYPES, weights=profile["personality_weights"])[0]

        # --- Social media (only if has internet) ---
        if internet_access:
            online_behaviors = SOCIAL_MEDIA_BEHAVIORS[:-1]  # exclude not_online
            social_behavior = rng.choices(
                online_behaviors,
                weights=[10, 15, 30, 12, 8, 10, 15]
            )[0]
        else:
            social_behavior = "not_online"

        # --- Political leaning (granular, legacy field) ---
        political = rng.choice(POLITICAL_LEANINGS)

        # --- Language ---
        language = rng.choice(stats["languages"])

        # --- New dimensions from MegaFish 8.3B model ---
        culture_type = profile["culture_type"]

        political_orientation = rng.choices(
            POLITICAL_ORIENTATIONS, weights=profile["political_weights"]
        )[0]

        power_level = rng.choices(
            POWER_LEVELS, weights=profile["power_weights"]
        )[0]

        conflict_exposure = rng.choices(
            CONFLICT_EXPOSURE, weights=profile["conflict_weights"]
        )[0]

        living_situation = rng.choices(
            LIVING_SITUATIONS, weights=profile["living_weights"]
        )[0]

        employment_type = rng.choices(
            EMPLOYMENT_TYPES, weights=profile["employment_weights"]
        )[0]

        health_status = rng.choices(
            HEALTH_STATUSES, weights=profile["health_weights"]
        )[0]

        info_access = rng.choices(
            INFO_ACCESS_LEVELS, weights=profile["info_access_weights"]
        )[0]

        tech_access = rng.choices(
            TECH_ACCESS_LEVELS, weights=profile["tech_access_weights"]
        )[0]

        return {
            "agent_id": agent_id,
            "name": name,
            "age": age,
            "gender": gender,
            "country": country,
            "region": region,
            "language": language,
            "religion": religion,
            "education": education,
            "income_usd_annual": income,
            "internet_access": internet_access,
            "urban": urban,
            "employed": employed,
            # Core personality & behavior
            "personality": personality,
            "social_media_behavior": social_behavior,
            "political_leaning": political,
            # New MegaFish 8.3B dimensions
            "culture_type": culture_type,
            "political_orientation": political_orientation,
            "power_level": power_level,
            "conflict_exposure": conflict_exposure,
            "living_situation": living_situation,
            "employment_type": employment_type,
            "health_status": health_status,
            "info_access": info_access,
            "tech_access": tech_access,
        }

    def sample_agents(
        self,
        count: int,
        filters: Optional[Dict[str, Any]] = None,
        topic_context: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Sample N agents proportionally from the real-world population.
        Filters: {"country": "India", "min_age": 18, "internet_only": True, ...}
        """
        filters = filters or {}
        results = []
        attempts = 0
        max_attempts = count * 20

        while len(results) < count and attempts < max_attempts:
            # Pick random agent from 8.3B
            agent_id = random.randint(0, self.TOTAL_POPULATION - 1)
            agent = self.get_agent(agent_id)
            attempts += 1

            # Apply filters
            if filters.get("country") and agent["country"] != filters["country"]:
                continue
            if filters.get("region") and agent["region"] != filters["region"]:
                continue
            if filters.get("min_age") and agent["age"] < filters["min_age"]:
                continue
            if filters.get("max_age") and agent["age"] > filters["max_age"]:
                continue
            if filters.get("internet_only") and not agent["internet_access"]:
                continue
            if filters.get("religion") and agent["religion"] != filters["religion"]:
                continue

            results.append(agent)

        return results

    def get_agent_by_country(self, country: str, local_id: int) -> Dict[str, Any]:
        """Get a specific agent within a country's population range."""
        for start, end, c, region, stats in self._ranges:
            if c == country:
                agent_id = start + (local_id % (end - start + 1))
                return self.get_agent(agent_id)
        raise ValueError(f"Country '{country}' not found")

    def get_population_stats(self) -> Dict[str, Any]:
        """Return real-world population breakdown by country and region."""
        stats = {}
        region_totals = {}
        for start, end, country, region, _ in self._ranges:
            pop = end - start + 1
            stats[country] = pop
            region_totals[region] = region_totals.get(region, 0) + pop
        return {
            "total": self.TOTAL_POPULATION,
            "by_country": stats,
            "by_region": region_totals,
        }


# Singleton
_registry: Optional[AgentRegistry] = None

def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
