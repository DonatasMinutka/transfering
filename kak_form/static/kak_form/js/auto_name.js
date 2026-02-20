document.addEventListener('DOMContentLoaded', function() {
    const tenantField = document.querySelector('[name="tenant"]');
    const siteField = document.querySelector('[name="site"]');
    const nameField = document.querySelector('#id_name');

const cityShortcuts = {
    'Akmenė': 'AKM',
    'Alytus': 'ALY',
    'Kauno': 'KNS',
    'Anykščiai': 'ANY',
    'Ariogala': 'ARG',
    'Baltoji Vokė': 'BVO',
    'Birštonas': 'BIR',
    'Biržai': 'BRZ',
    'Daugai': 'DAU',
    'Druskininkai': 'DRS',
    'Dūkštas': 'DUK',
    'Dusetos': 'DUS',
    'Eišiškės': 'EIS',
    'Elektrėnai': 'ELK',
    'Ežerėlis': 'EZE',
    'Gargždai': 'GAR',
    'Garliava': 'GRL',
    'Gelgaudiškis': 'GEL',
    'Grigiškės': 'GRG',
    'Ignalina': 'IGN',
    'Jieznas': 'JIE',
    'Jonava': 'JON',
    'Joniškėlis': 'JNK',
    'Joniškis': 'JNS',
    'Jurbarkas': 'JUR',
    'Kaišiadorys': 'KAI',
    'Kalvarija': 'KAL',
    'Kaunas': 'KNS',
    'Kavarskas': 'KAV',
    'Kazlų Rūda': 'KZR',
    'Kėdainiai': 'KDN',
    'Kelmė': 'KEL',
    'Kybartai': 'KYB',
    'Klaipėda': 'KLP',
    'Kretinga': 'KRE',
    'Kudirkos Naumiestis': 'KUD',
    'Kupiškis': 'KUP',
    'Kuršėnai': 'KUR',
    'Lazdijai': 'LAZ',
    'Lentvaris': 'LEN',
    'Linkuva': 'LIN',
    'Marijampolė': 'MRJ',
    'Mažeikiai': 'MAZ',
    'Molėtai': 'MOL',
    'Naujoji Akmenė': 'NAK',
    'Nemenčinė': 'NEM',
    'Neringa': 'NER',
    'Obeliai': 'OBE',
    'Pabradė': 'PAB',
    'Pagėgiai': 'PAG',
    'Pakruojis': 'PAK',
    'Palanga': 'PLG',
    'Pandėlys': 'PAN',
    'Panemunė': 'PNM',
    'Panevėžys': 'PNV',
    'Pasvalys': 'PAS',
    'Plungė': 'PLU',
    'Priekulė': 'PRI',
    'Prienai': 'PRN',
    'Radviliškis': 'RAD',
    'Ramygala': 'RAM',
    'Raseiniai': 'RAS',
    'Rietavas': 'RIE',
    'Rokiškis': 'ROK',
    'Rūdiškės': 'RUD',
    'Salantai': 'SAL',
    'Seda': 'SED',
    'Simnas': 'SIM',
    'Skaudvilė': 'SKA',
    'Skuodas': 'SKU',
    'Smalininkai': 'SMA',
    'Subačius': 'SUB',
    'Šakiai': 'SAK',
    'Šalčininkai': 'SLC',
    'Šeduva': 'SEV',
    'Šiauliai': 'SIA',
    'Šilalė': 'SIL',
    'Šilutė': 'SLT',
    'Širvintos': 'SRV',
    'Švenčionėliai': 'SVL',
    'Švenčionys': 'SVC',
    'Tauragė': 'TRG',
    'Telšiai': 'TEL',
    'Tytuvėnai': 'TYT',
    'Trakai': 'TRA',
    'Troškūnai': 'TRO',
    'Ukmergė': 'UKM',
    'Utena': 'UTE',
    'Užventis': 'UZV',
    'Vabalninkas': 'VAB',
    'Varėna': 'VAR',
    'Varniai': 'VRN',
    'Veisiejai': 'VEI',
    'Venta': 'VEN',
    'Viekšniai': 'VIE',
    'Vievis': 'VIV',
    'Vilkaviškis': 'VLK',
    'Vilkija': 'VKJ',
    'Vilnius': 'VIL',
    'Virbalis': 'VRB',
    'Visaginas': 'VIS',
    'Zarasai': 'ZRS',
    'Žagarė': 'ZAG',
    'Žiežmariai': 'ZIE'
};
function removeLithuanianDiacritics(str) {
    const map = {
        'ą': 'a', 'Ą': 'A',
        'č': 'c', 'Č': 'C',
        'ę': 'e', 'Ę': 'E',
        'ė': 'e', 'Ė': 'E',
        'į': 'i', 'Į': 'I',
        'š': 's', 'Š': 'S',
        'ų': 'u', 'Ų': 'U',
        'ū': 'u', 'Ū': 'U',
        'ž': 'z', 'Ž': 'Z'
    };
    
    return str.replace(/[ąčęėįšųūžĄČĘĖĮŠŲŪŽ]/g, char => map[char] || char);
}

function updateName() {
    let tenant = tenantField.options[tenantField.selectedIndex]?.text || '';
    let site = siteField.options[siteField.selectedIndex]?.text || '';
    const regex = /^(?:\S+\.\s+)?(\S+).*?\s+(g\.|pl\.|pr\.|al\.|tel\.|tak\.|skg\.|a\.|kl\.|aplinkl\.|bul\.|k\.|skl\.|kel\.|skv\.|aklg\.)\s+([^,]+),\s+(.+)$/;
    const match = site.match(regex);
    
    let matches0 = '';
    let matches1 = '';
    let matches2 = '';
    
    if (match) {
        matches0 = removeLithuanianDiacritics(match[1]).substring(0, 3);
        matches1 = match[3]; 
        matches2 = cityShortcuts[match[4]] || removeLithuanianDiacritics(match[4]).substring(0, 3).toUpperCase();
    }
        
    const count = (str) => str.trim().split(/\s+/).length;
    tenant = removeLithuanianDiacritics(tenant);

    if (count(tenant) > 1) {
        tenant = tenant.trim()
            .split(/\s+/)
            .map(word => word[0].toUpperCase())
            .join('');
    } else if (tenant.length > 10) {
        tenant = tenant.substring(0, 3);
    }
    
    if (tenant && site) {
        const autoName = `${tenant}_${matches0}${matches1}_${matches2}`.toUpperCase()
            .replace(/\s+/g, '_')
            .replace(/[^A-Z0-9_-]/g, '');
        nameField.value = autoName;
    }
}

    
    
    if (tenantField) tenantField.addEventListener('change', updateName);
    if (siteField) siteField.addEventListener('change', updateName);
});