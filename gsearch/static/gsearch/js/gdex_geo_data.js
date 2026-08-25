/* ============================================================
   GDEX — Geographic reference data for the location filter
   Loaded before search_data.js on search.html.

   Add new countries/states/provinces here as they show up in
   dataset location facets. See classifyBucket() in search_data.js
   for how these are used.
   ============================================================ */

window.GDEX_GEO = (function () {
    var US_STATES = {};
    ['ALABAMA','ALASKA','ARIZONA','ARKANSAS','CALIFORNIA','COLORADO','CONNECTICUT',
     'DELAWARE','FLORIDA','GEORGIA','HAWAII','IDAHO','ILLINOIS','INDIANA','IOWA',
     'KANSAS','KENTUCKY','LOUISIANA','MAINE','MARYLAND','MASSACHUSETTS','MICHIGAN',
     'MINNESOTA','MISSISSIPPI','MISSOURI','MONTANA','NEBRASKA','NEVADA',
     'NEW HAMPSHIRE','NEW JERSEY','NEW MEXICO','NEW YORK','NORTH CAROLINA',
     'NORTH DAKOTA','OHIO','OKLAHOMA','OREGON','PENNSYLVANIA','RHODE ISLAND',
     'SOUTH CAROLINA','SOUTH DAKOTA','TENNESSEE','TEXAS','UTAH','VERMONT',
     'VIRGINIA','WASHINGTON','WEST VIRGINIA','WISCONSIN','WYOMING',
     'DISTRICT OF COLUMBIA'].forEach(function (s) { US_STATES[s] = true; });

    var CA_PROVS = {};
    ['ALBERTA','BRITISH COLUMBIA','MANITOBA','NEW BRUNSWICK',
     'NEWFOUNDLAND AND LABRADOR','NORTHWEST TERRITORIES','NOVA SCOTIA','NUNAVUT',
     'ONTARIO','PRINCE EDWARD ISLAND','QUEBEC','SASKATCHEWAN','YUKON']
        .forEach(function (p) { CA_PROVS[p] = true; });

    var COUNTRY_CONT = {
        'CANADA':'North America','MEXICO':'North America','GREENLAND':'North America',
        'CUBA':'North America','PUERTO RICO':'North America','BERMUDA':'North America',
        'BELIZE':'North America','COSTA RICA':'North America','EL SALVADOR':'North America',
        'GUATEMALA':'North America','HONDURAS':'North America','NICARAGUA':'North America',
        'PANAMA':'North America','HAITI':'North America','DOMINICAN REPUBLIC':'North America',
        'JAMAICA':'North America','TRINIDAD AND TOBAGO':'North America',
        'BRAZIL':'South America','ARGENTINA':'South America','CHILE':'South America',
        'COLOMBIA':'South America','PERU':'South America','VENEZUELA':'South America',
        'ECUADOR':'South America','BOLIVIA':'South America','PARAGUAY':'South America',
        'URUGUAY':'South America','GUYANA':'South America','SURINAME':'South America',
        'UNITED KINGDOM':'Europe','FRANCE':'Europe','GERMANY':'Europe','ITALY':'Europe',
        'SPAIN':'Europe','PORTUGAL':'Europe','NETHERLANDS':'Europe','BELGIUM':'Europe',
        'SWITZERLAND':'Europe','AUSTRIA':'Europe','SWEDEN':'Europe','NORWAY':'Europe',
        'DENMARK':'Europe','FINLAND':'Europe','IRELAND':'Europe','GREECE':'Europe',
        'POLAND':'Europe','CZECH REPUBLIC':'Europe','SLOVAKIA':'Europe',
        'HUNGARY':'Europe','ROMANIA':'Europe','BULGARIA':'Europe','CROATIA':'Europe',
        'UKRAINE':'Europe','RUSSIA':'Europe',
        'CHINA':'Asia','JAPAN':'Asia','INDIA':'Asia','SOUTH KOREA':'Asia',
        'NORTH KOREA':'Asia','TAIWAN':'Asia','INDONESIA':'Asia','MALAYSIA':'Asia',
        'PHILIPPINES':'Asia','THAILAND':'Asia','VIETNAM':'Asia','CAMBODIA':'Asia',
        'MYANMAR':'Asia','LAOS':'Asia','SINGAPORE':'Asia','BANGLADESH':'Asia',
        'SRI LANKA':'Asia','NEPAL':'Asia','PAKISTAN':'Asia','AFGHANISTAN':'Asia',
        'IRAN':'Asia','IRAQ':'Asia','SAUDI ARABIA':'Asia','TURKEY':'Asia',
        'SYRIA':'Asia','JORDAN':'Asia','ISRAEL':'Asia','LEBANON':'Asia',
        'OMAN':'Asia','YEMEN':'Asia','KUWAIT':'Asia',
        'UNITED ARAB EMIRATES':'Asia','UAE':'Asia','MONGOLIA':'Asia',
        'KAZAKHSTAN':'Asia','UZBEKISTAN':'Asia','TAJIKISTAN':'Asia',
        'KYRGYZSTAN':'Asia','TURKMENISTAN':'Asia',
        'NIGERIA':'Africa','ETHIOPIA':'Africa','EGYPT':'Africa',
        'SOUTH AFRICA':'Africa','KENYA':'Africa','GHANA':'Africa',
        'TANZANIA':'Africa','ALGERIA':'Africa','ANGOLA':'Africa',
        'MOZAMBIQUE':'Africa','CAMEROON':'Africa','NIGER':'Africa',
        'MALI':'Africa','SENEGAL':'Africa','CHAD':'Africa','SOMALIA':'Africa',
        'RWANDA':'Africa','ZAMBIA':'Africa','ZIMBABWE':'Africa',
        'MOROCCO':'Africa','TUNISIA':'Africa','LIBYA':'Africa','SUDAN':'Africa',
        'SOUTH SUDAN':'Africa',
        'AUSTRALIA':'Oceania','NEW ZEALAND':'Oceania',
        'PAPUA NEW GUINEA':'Oceania','FIJI':'Oceania'
    };

    var GCMD_TOP = { 'CONTINENT':true, 'OCEAN':true, 'GEOGRAPHIC REGION':true,
                     'VERTICAL LOCATION':true, 'WATERSHED':true };

    var CONT_ORDER = ['North America','South America','Europe','Asia',
                      'Africa','Oceania','Polar Regions','Ocean Basins'];

    return {
        US_STATES: US_STATES,
        CA_PROVS: CA_PROVS,
        COUNTRY_CONT: COUNTRY_CONT,
        GCMD_TOP: GCMD_TOP,
        CONT_ORDER: CONT_ORDER
    };
}());