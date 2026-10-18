# -*- coding: utf-8 -*-
"""Generate web/i18n.json.

Keys are the English source strings themselves, so a missing entry falls back
to English instead of showing a key name. Service names are keyed by code.

    python scripts/make_i18n.py
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["es", "fr", "zh", "ar"]

META = {
    "en": {"name": "English",  "dir": "ltr", "short": "EN"},
    "es": {"name": "Espanol",  "dir": "ltr", "short": "ES", "native": "Español"},
    "fr": {"name": "Francais", "dir": "ltr", "short": "FR", "native": "Français"},
    "zh": {"name": "Chinese",  "dir": "ltr", "short": "ZH", "native": "中文"},
    "ar": {"name": "Arabic",   "dir": "rtl", "short": "AR", "native": "العربية"},
}

# ---------------------------------------------------------------- UI strings
# order: es, fr, zh, ar
UI = {
 "Hospital price &amp; quality &middot; Lehigh Valley": [
  "Precios y calidad hospitalaria &middot; Valle de Lehigh",
  "Prix et qualité hospitaliers &middot; Vallée de Lehigh",
  "医院价格与质量 &middot; 利高谷",
  "أسعار وجودة المستشفيات &middot; وادي ليهاي"],
 "What will this actually cost?": [
  "¿Cuánto costará realmente?",
  "Combien cela coûtera-t-il vraiment ?",
  "这到底要花多少钱？",
  "كم ستكلف هذه الخدمة فعلياً؟"],
 "High contrast": [
  "Alto contraste", "Contraste élevé", "高对比度",
  "تباين عالٍ"],
 "High contrast on": [
  "Alto contraste activado", "Contraste élevé activé", "高对比度已开启",
  "تباين عالٍ مفعّل"],
 "ZIP code": ["Código postal", "Code postal", "邮政编码", "الرمز البريدي"],
 "Insurance provider": ["Aseguradora", "Assureur", "保险公司", "شركة التأمين"],
 "Plan": ["Plan", "Formule", "保险计划", "الخطة"],
 "Medical procedure": ["Procedimiento médico", "Acte médical", "医疗服务", "الإجراء الطبي"],
 "Search": ["Buscar", "Rechercher", "搜索", "بحث"],
 "Search 89 procedures or a CPT code": [
  "Busque entre 89 procedimientos o un código CPT",
  "Rechercher parmi 89 actes ou un code CPT",
  "搜索 89 项服务或 CPT 代码",
  "ابحث في 89 إجراءً أو برمز CPT"],
 "Select your insurer&hellip;": [
  "Elija su aseguradora&hellip;", "Choisissez votre assureur&hellip;",
  "选择您的保险公司&hellip;", "اختر شركة التأمين&hellip;"],
 "Any plan": ["Cualquier plan", "Toutes formules", "任何计划", "أي خطة"],
 "Browse": ["Explorar", "Parcourir", "浏览", "تصفّح"],
 "Common": ["Frecuentes", "Courants", "常见", "الأكثر شيوعاً"],
 "Symptom": ["Síntoma", "Symptôme", "症状", "الأعراض"],
 "Insurer": ["Aseguradora", "Assureur", "保险公司", "التأمين"],
 "Self-pay / cash": ["Pago propio / efectivo", "Paiement direct / espèces", "自费 / 现金", "دفع ذاتي / نقداً"],
 "What matters most to you?": [
  "¿Qué es lo más importante para usted?",
  "Qu'est-ce qui compte le plus pour vous ?",
  "您最看重哪一点？",
  "ما الأهم بالنسبة لك؟"],
 "Drag to reorder, or use the arrows. Top of the list counts most.": [
  "Arrastre para reordenar o use las flechas. Lo primero pesa más.",
  "Faites glisser pour réorganiser, ou utilisez les flèches. Le premier compte le plus.",
  "拖动排序，或使用箭头。最上方的权重最大。",
  "اسحب لإعادة الترتيب، أو استخدم الأسهم. الأعلى هو الأكثر تأثيراً."],
 "Hospitals": ["Hospitales", "Hôpitaux", "医院", "المستشفيات"],
 "Aftercare": ["Después del procedimiento", "Suivi après l'acte", "术后事项", "الرعاية بعد الإجراء"],
 "Estimate my bill": ["Calcular mi factura", "Estimer ma facture", "费用估算", "قدّر فاتورتي"],
 # factors
 "Price": ["Precio", "Prix", "价格", "السعر"],
 "Distance": ["Distancia", "Distance", "距离", "المسافة"],
 "Patient safety": ["Seguridad del paciente", "Sécurité des patients", "患者安全", "سلامة المرضى"],
 "Quality rating": ["Calificación de calidad", "Note de qualité", "质量评级", "تقييم الجودة"],
 "Readmissions": ["Reingresos", "Réadmissions", "再入院率", "إعادة الدخول"],
 "Lowest negotiated rate": ["Tarifa negociada más baja", "Tarif négocié le plus bas", "协议价最低", "أقل سعر متفاوض عليه"],
 "Closest to your ZIP": ["Más cerca de su código postal", "Le plus proche de votre code postal", "距您邮编最近", "الأقرب إلى رمزك البريدي"],
 "CMS safety measures": ["Medidas de seguridad de CMS", "Indicateurs de sécurité CMS", "CMS 安全指标", "مؤشرات السلامة من CMS"],
 "CMS overall star rating": ["Calificación general de CMS", "Note globale CMS en étoiles", "CMS 总体星级", "تقييم CMS بالنجوم"],
 "CMS readmission measures": ["Medidas de reingreso de CMS", "Indicateurs de réadmission CMS", "CMS 再入院指标", "مؤشرات إعادة الدخول من CMS"],
 "weight": ["peso", "poids", "权重", "الوزن"],
 "Move {x} up": ["Subir {x}", "Monter {x}", "上移 {x}", "تحريك {x} لأعلى"],
 "Move {x} down": ["Bajar {x}", "Descendre {x}", "下移 {x}", "تحريك {x} لأسفل"],
 # status / validation
 "Loading price data&hellip;": ["Cargando datos de precios&hellip;", "Chargement des tarifs&hellip;", "正在加载价格数据&hellip;", "جارٍ تحميل بيانات الأسعار&hellip;"],
 "Looking up rates&hellip;": ["Consultando tarifas&hellip;", "Recherche des tarifs&hellip;", "正在查询价格&hellip;", "جارٍ البحث عن الأسعار&hellip;"],
 "a 5-digit ZIP code": ["un código postal de 5 dígitos", "un code postal à 5 chiffres", "5 位邮政编码", "رمزاً بريدياً من 5 أرقام"],
 "your insurance provider": ["su aseguradora", "votre assureur", "您的保险公司", "شركة التأمين الخاصة بك"],
 "a medical procedure from the list": ["un procedimiento de la lista", "un acte de la liste", "列表中的一项服务", "إجراءً طبياً من القائمة"],
 "Please enter {x} before searching.": [
  "Introduzca {x} antes de buscar.", "Veuillez saisir {x} avant de lancer la recherche.",
  "请先输入{x}再搜索。", "يرجى إدخال {x} قبل البحث."],
 "and": ["y", "et", "和", "و"],
 "Nothing matches that in the 89-service sample. Try &ldquo;MRI&rdquo;, &ldquo;colonoscopy&rdquo;, &ldquo;ER&rdquo; or a CPT code such as 72148.": [
  "No hay coincidencias en la muestra de 89 servicios. Pruebe &ldquo;resonancia&rdquo;, &ldquo;colonoscopia&rdquo;, &ldquo;urgencias&rdquo; o un código CPT como 72148.",
  "Aucun résultat dans l'échantillon de 89 actes. Essayez &ldquo;IRM&rdquo;, &ldquo;coloscopie&rdquo;, &ldquo;urgences&rdquo; ou un code CPT comme 72148.",
  "在 89 项服务样本中未找到匹配项。请尝试“磁共振”、“结肠镜”、“急诊”或 CPT 代码（如 72148）。",
  "لا يوجد تطابق ضمن عينة الخدمات الـ 89. جرّب «الرنين المغناطيسي» أو «تنظير القولون» أو «الطوارئ» أو رمز CPT مثل 72148."],
 # results
 "match": ["coincidencia", "adéquation", "匹配度", "التطابق"],
 "typical negotiated rate": ["tarifa negociada habitual", "tarif négocié habituel", "典型协议价", "السعر المتفاوض عليه المعتاد"],
 "no data": ["sin datos", "aucune donnée", "无数据", "لا توجد بيانات"],
 "not published": ["no publicado", "non publié", "未公布", "غير منشور"],
 "inpatient": ["hospitalización", "hospitalisation", "住院", "داخل المستشفى"],
 "outpatient": ["ambulatorio", "ambulatoire", "门诊", "العيادات الخارجية"],
 "Directions &rarr;": ["Cómo llegar &rarr;", "Itinéraire &rarr;", "导航 &rarr;", "الاتجاهات &rarr;"],
 "Rates by plan": ["Tarifas por plan", "Tarifs par formule", "各计划价格", "الأسعار حسب الخطة"],
 "Commonly billed alongside": [
  "Suele facturarse junto con esto", "Souvent facturé en plus",
  "通常一并计费的项目", "يُفوتر عادةً إلى جانب ذلك"],
 "Selected extras": ["Extras seleccionados", "Suppléments sélectionnés", "已选附加项", "الإضافات المحددة"],
 "Typical costs for {x}": [
  "Costos habituales para {x}", "Coûts habituels pour {x}",
  "{x} 的典型费用", "التكاليف المعتادة لـ {x}"],
 # bill estimator
 "Standard PPO": ["PPO estándar", "PPO standard", "标准 PPO", "PPO قياسية"],
 "High-deductible plan": ["Plan con deducible alto", "Formule à franchise élevée", "高免赔额计划", "خطة بخصم مرتفع"],
 "Deductible already met": ["Deducible ya cubierto", "Franchise déjà atteinte", "免赔额已达成", "تم بلوغ الخصم المقتطع"],
 "Medicare Part B": ["Medicare Parte B", "Medicare partie B", "Medicare B 部分", "Medicare الجزء B"],
 "Uninsured / self-pay": ["Sin seguro / pago propio", "Sans assurance / paiement direct", "无保险 / 自费", "غير مؤمّن / دفع ذاتي"],
 "Pick a situation, or type your own numbers below.": [
  "Elija una situación o escriba sus propias cifras abajo.",
  "Choisissez une situation, ou saisissez vos propres chiffres ci-dessous.",
  "选择一种情况，或在下方输入您自己的数字。",
  "اختر حالة، أو أدخل أرقامك أدناه."],
 "Deductible": ["Deducible", "Franchise", "免赔额", "الخصم المقتطع"],
 "remaining": ["restante", "restante", "剩余", "المتبقي"],
 "Coinsurance": ["Coaseguro", "Coassurance", "共保比例", "التأمين المشترك"],
 "Flat copay (if any)": ["Copago fijo (si lo hay)", "Ticket modérateur fixe (le cas échéant)", "固定自付额（如有）", "مبلغ ثابت مشترك (إن وجد)"],
 "Out-of-pocket max": ["Máximo de gastos propios", "Plafond de reste à charge", "自付上限", "الحد الأقصى للنفقات الشخصية"],
 "left": ["restante", "restant", "剩余", "المتبقي"],
 "you": ["usted", "vous", "您", "أنت"],
 "Run a search first.": ["Realice una búsqueda primero.", "Lancez d'abord une recherche.", "请先进行搜索。", "قم بالبحث أولاً."],
 "You would pay about": ["Usted pagaría aproximadamente", "Vous paieriez environ", "您大约需支付", "ستدفع حوالي"],
 "pays": ["paga", "paie", "支付", "تدفع"],
 "Negotiated rate for the procedure": [
  "Tarifa negociada del procedimiento", "Tarif négocié de l'acte",
  "该项目的协议价", "السعر المتفاوض عليه للإجراء"],
 "Applied to your deductible": [
  "Aplicado a su deducible", "Imputé sur votre franchise",
  "计入您的免赔额", "يُحتسب من الخصم المقتطع"],
 "Left after the deductible": [
  "Resto tras el deducible", "Reste après la franchise",
  "扣除免赔额后剩余", "المتبقي بعد الخصم"],
 "Capped by your out-of-pocket maximum": [
  "Limitado por su máximo de gastos propios", "Plafonné par votre reste à charge maximum",
  "受自付上限限制", "محدود بسقف نفقاتك الشخصية"],
 "Extra line items you ticked": [
  "Partidas adicionales marcadas", "Lignes supplémentaires cochées",
  "您勾选的附加项目", "البنود الإضافية التي حددتها"],
 "Total allowed amount": ["Importe total permitido", "Montant total admis", "允许总额", "إجمالي المبلغ المسموح"],
 "Discounted cash price": ["Precio en efectivo con descuento", "Prix comptant remisé", "现金优惠价", "سعر نقدي مخفّض"],
 "List (chargemaster) price": ["Precio de lista", "Prix catalogue", "挂牌价", "السعر المعلن"],
 "Hospital's discounted cash price": [
  "Precio en efectivo del hospital", "Prix comptant remisé de l'hôpital",
  "医院的现金优惠价", "سعر المستشفى النقدي المخفّض"],
 "Hospital's list price": ["Precio de lista del hospital", "Prix catalogue de l'hôpital", "医院挂牌价", "السعر المعلن للمستشفى"],
 "Traditional Medicare has no out-of-pocket maximum": [
  "Medicare tradicional no tiene máximo de gastos propios",
  "Le Medicare classique n'a aucun plafond de reste à charge",
  "传统 Medicare 没有自付上限",
  "Medicare التقليدي لا يضع حداً أقصى للنفقات"],
 "Print or save this summary": [
  "Imprimir o guardar este resumen", "Imprimer ou enregistrer ce résumé",
  "打印或保存此摘要", "اطبع أو احفظ هذا الملخص"],
 "After the procedure": ["Después del procedimiento", "Après l'acte", "术后", "بعد الإجراء"],
 "How to read this": ["Cómo leer esto", "Comment lire ces chiffres", "如何解读", "كيف تقرأ هذه الأرقام"],
}

CAT = {
 "Imaging": ["Imágenes", "Imagerie", "影像检查", "التصوير"],
 "Cardiology": ["Cardiología", "Cardiologie", "心脏科", "أمراض القلب"],
 "Laboratory": ["Laboratorio", "Laboratoire", "化验", "المختبر"],
 "Evaluation & Management": ["Consulta médica", "Consultation", "诊疗评估", "الفحص والمتابعة"],
 "Therapy": ["Terapia", "Rééducation", "理疗", "العلاج الطبيعي"],
 "Behavioral Health": ["Salud mental", "Santé mentale", "心理健康", "الصحة النفسية"],
 "Preventive": ["Prevención", "Prévention", "预防", "الوقاية"],
 "Surgery": ["Cirugía", "Chirurgie", "外科手术", "الجراحة"],
 "Endoscopy": ["Endoscopia", "Endoscopie", "内镜检查", "التنظير"],
 "Pain Management": ["Manejo del dolor", "Traitement de la douleur", "疼痛管理", "علاج الألم"],
 "Emergency": ["Urgencias", "Urgences", "急诊", "الطوارئ"],
 "Ancillary": ["Servicios complementarios", "Services annexes", "辅助服务", "خدمات مساندة"],
 "Inpatient Medical": ["Hospitalización médica", "Hospitalisation médicale", "住院内科", "إقامة طبية"],
 "Inpatient Surgical": ["Hospitalización quirúrgica", "Hospitalisation chirurgicale", "住院外科", "إقامة جراحية"],
 "Inpatient Obstetric": ["Hospitalización obstétrica", "Hospitalisation obstétricale", "住院产科", "إقامة للولادة"],
 "Obstetrics": ["Obstetricia", "Obstétrique", "产科", "التوليد"],
}

CATGROUP = {
 "Imaging & scans": ["Imágenes y escaneos", "Imagerie et scanners", "影像与扫描", "التصوير والمسح"],
 "Lab tests": ["Análisis de laboratorio", "Analyses de laboratoire", "化验检查", "تحاليل المختبر"],
 "Office & outpatient": ["Consulta y ambulatorio", "Consultation et ambulatoire", "门诊与常规就诊", "العيادات الخارجية"],
 "Surgery & procedures": ["Cirugía y procedimientos", "Chirurgie et actes", "手术与操作", "الجراحة والإجراءات"],
 "Inpatient stays": ["Estancias hospitalarias", "Séjours hospitaliers", "住院", "الإقامة بالمستشفى"],
}

COND = {
 "Flu or bad cold": ["Gripe o resfriado fuerte", "Grippe ou gros rhume", "流感或重感冒", "الإنفلونزا أو الزكام الشديد"],
 "Pneumonia": ["Neumonía", "Pneumonie", "肺炎", "التهاب الرئة"],
 "Chest pain": ["Dolor en el pecho", "Douleur thoracique", "胸痛", "ألم في الصدر"],
 "Stroke signs": ["Signos de derrame cerebral", "Signes d'AVC", "中风征兆", "علامات السكتة الدماغية"],
 "Trouble breathing": ["Dificultad para respirar", "Difficultés respiratoires", "呼吸困难", "صعوبة في التنفس"],
 "Broken bone or injury": ["Fractura o lesión", "Fracture ou blessure", "骨折或外伤", "كسر أو إصابة"],
 "Urinary infection": ["Infección urinaria", "Infection urinaire", "尿路感染", "التهاب المسالك البولية"],
 "Pregnancy and birth": ["Embarazo y parto", "Grossesse et accouchement", "妊娠与分娩", "الحمل والولادة"],
 "Back pain": ["Dolor de espalda", "Mal de dos", "背痛", "ألم الظهر"],
 "Knee or hip pain": ["Dolor de rodilla o cadera", "Douleur au genou ou à la hanche", "膝部或髀部疼痛", "ألم الركبة أو الورك"],
 "Stomach pain": ["Dolor abdominal", "Douleur abdominale", "腹痛", "ألم البطن"],
 "Diabetes check-up": ["Control de diabetes", "Suivi du diabète", "糖尿病复查", "متابعة السكري"],
 "Depression or anxiety": ["Depresión o ansiedad", "Dépression ou anxiété", "抑郁或焦虑", "الاكتئاب أو القلق"],
 "Cancer screening": ["Detección de cáncer", "Dépistage du cancer", "癌症筛查", "الكشف المبكر عن السرطان"],
 "Severe infection (sepsis)": ["Infección grave (sepsis)", "Infection grave (sepsis)", "严重感染（败血症）", "عدوى شديدة (إنتان الدم)"],
}

POP = {
 "MRI lower back": ["Resonancia lumbar", "IRM lombaire", "腰部磁共振", "رنين مغناطيسي لأسفل الظهر"],
 "CT head": ["TAC de cabeza", "Scanner cérébral", "头部 CT", "أشعة مقطعية للرأس"],
 "Mammogram": ["Mamografía", "Mammographie", "乳腺 X 光检查", "تصوير الثدي"],
 "ER visit (level 4)": ["Urgencias (nivel 4)", "Urgences (niveau 4)", "急诊（4 级）", "زيارة الطوارئ (المستوى 4)"],
 "Colonoscopy": ["Colonoscopia", "Coloscopie", "结肠镜检查", "تنظير القولون"],
 "Childbirth": ["Parto", "Accouchement", "分娩", "الولادة"],
 "Knee replacement": ["Prótesis de rodilla", "Prothèse du genou", "膝关节置换", "استبدال مفصل الركبة"],
 "Bloodwork panel": ["Panel de sangre", "Bilan sanguin", "血液检查套餐", "فحوصات الدم"],
}

# ------------------------------------------------------------- service names
SVC = {
 "00810": ["Anestesia para endoscopia digestiva baja", "Anesthésie pour endoscopie digestive basse", "下消化道内镜麻醉", "تخدير لتنظير الجهاز الهضمي السفلي"],
 "36415": ["Extracción de sangre de rutina", "Prise de sang de routine", "常规抽血", "سحب دم روتيني"],
 "88312": ["Tinción especial de patología", "Coloration spéciale en anatomopathologie", "病理特殊染色", "صبغة خاصة لعينة مرضية"],
 "96365": ["Infusión intravenosa, primera hora", "Perfusion intraveineuse, première heure", "静脉输液（首小时）", "تسريب وريدي – الساعة الأولى"],
 "96374": ["Inyección intravenosa de un medicamento", "Injection intraveineuse d'un médicament", "静脉推注单一药物", "حقن وريدي لدواء واحد"],
 "99152": ["Sedación moderada, primeros 15 minutos", "Sédation modérée, 15 premières minutes", "中度镇静（前 15 分钟）", "تهدئة متوسطة – أول 15 دقيقة"],
 "99153": ["Sedación moderada, cada 15 minutos extra", "Sédation modérée, par tranche de 15 min", "中度镇静（每增 15 分钟）", "تهدئة متوسطة – كل 15 دقيقة إضافية"],
 "A0425": ["Ambulancia, por milla recorrida", "Ambulance, par mile parcouru", "救护车每英里里程", "سيارة إسعاف – لكل ميل"],
 "A0427": ["Ambulancia de soporte vital avanzado", "Ambulance de réanimation avancée", "高级生命支持救护车", "إسعاف بدعم حياتي متقدم"],
 "A0429": ["Ambulancia de soporte vital básico", "Ambulance de secours de base", "基础生命支持救护车", "إسعاف بدعم حياتي أساسي"],
 "J1885": ["Inyección de ketorolaco para el dolor", "Injection de kétorolac contre la douleur", "酎洛美酮镇痛注射", "حقنة كيتورولاك للألم"],
 "90791": ["Evaluación psiquiátrica diagnóstica", "Évaluation psychiatrique diagnostique", "精神科诊断评估", "تقييم نفسي تشخيصي"],
 "90834": ["Psicoterapia, 45 minutos", "Psychothérapie, 45 minutes", "心理治疗 45 分钟", "علاج نفسي 45 دقيقة"],
 "90837": ["Psicoterapia, 60 minutos", "Psychothérapie, 60 minutes", "心理治疗 60 分钟", "علاج نفسي 60 دقيقة"],
 "93000": ["Electrocardiograma con interpretación", "Électrocardiogramme avec interprétation", "心电图及报告", "تخطيط قلب مع التفسير"],
 "93306": ["Ecocardiograma completo con Doppler", "Échocardiographie complète avec Doppler", "全套心超彩超", "تخطيط صدى القلب الكامل مع دوبلر"],
 "93880": ["Ecografía dúplex carotídea", "Écho-doppler des carotides", "颈动脉双功能超声", "تصوير مزدوج للشريان السباتي"],
 "99281": ["Urgencias, nivel 1", "Urgences, niveau 1", "急诊 1 级", "طوارئ المستوى 1"],
 "99282": ["Urgencias, nivel 2", "Urgences, niveau 2", "急诊 2 级", "طوارئ المستوى 2"],
 "99283": ["Urgencias, nivel 3", "Urgences, niveau 3", "急诊 3 级", "طوارئ المستوى 3"],
 "99284": ["Urgencias, nivel 4", "Urgences, niveau 4", "急诊 4 级", "طوارئ المستوى 4"],
 "99285": ["Urgencias, nivel 5", "Urgences, niveau 5", "急诊 5 级", "طوارئ المستوى 5"],
 "43235": ["Endoscopia digestiva alta diagnóstica", "Endoscopie digestive haute diagnostique", "上消化道内镜检查", "تنظير علوي تشخيصي"],
 "43239": ["Endoscopia digestiva alta con biopsia", "Endoscopie digestive haute avec biopsie", "上消化道内镜及活检", "تنظير علوي مع خزعة"],
 "45378": ["Colonoscopia diagnóstica", "Coloscopie diagnostique", "诊断性结肠镜", "تنظير قولون تشخيصي"],
 "45380": ["Colonoscopia con biopsia", "Coloscopie avec biopsie", "结肠镜及活检", "تنظير قولون مع خزعة"],
 "45385": ["Colonoscopia con extirpación de pólipo", "Coloscopie avec polypectomie à l'anse", "结肠镜圈套切除息肉", "تنظير قولون مع استئصال زائدة"],
 "99203": ["Consulta, paciente nuevo, nivel 3", "Consultation, nouveau patient, niveau 3", "初诊 3 级", "زيارة مريض جديد – المستوى 3"],
 "99204": ["Consulta, paciente nuevo, nivel 4", "Consultation, nouveau patient, niveau 4", "初诊 4 级", "زيارة مريض جديد – المستوى 4"],
 "99213": ["Consulta, paciente conocido, nivel 3", "Consultation, patient connu, niveau 3", "复诊 3 级", "زيارة مريض حالي – المستوى 3"],
 "99214": ["Consulta, paciente conocido, nivel 4", "Consultation, patient connu, niveau 4", "复诊 4 级", "زيارة مريض حالي – المستوى 4"],
 "70450": ["TAC de cabeza sin contraste", "Scanner cérébral sans produit de contraste", "头部 CT（平扫）", "أشعة مقطعية للرأس بدون صبغة"],
 "70553": ["Resonancia cerebral con y sin contraste", "IRM cérébrale avec et sans contraste", "脑部磁共振（平扫+增强）", "رنين مغناطيسي للدماغ بصبغة وبدونها"],
 "71046": ["Radiografía de tórax, 2 proyecciones", "Radiographie du thorax, 2 incidences", "胸部 X 光（2 位）", "أشعة سينية للصدر – صورتان"],
 "71250": ["TAC de tórax sin contraste", "Scanner thoracique sans contraste", "胸部 CT（平扫）", "أشعة مقطعية للصدر بدون صبغة"],
 "72110": ["Radiografía lumbar, 4 o más proyecciones", "Radiographie lombaire, 4 incidences ou plus", "腰椎 X 光（4 位以上）", "أشعة سينية للفقرات القطنية"],
 "72148": ["Resonancia lumbar sin contraste", "IRM lombaire sans contraste", "腰椎磁共振（平扫）", "رنين مغناطيسي قطني بدون صبغة"],
 "73721": ["Resonancia de articulación de pierna", "IRM d'articulation du membre inférieur", "下肢关节磁共振", "رنين مغناطيسي لمفصل الطرف السفلي"],
 "74177": ["TAC de abdomen y pelvis con contraste", "Scanner abdomino-pelvien avec contraste", "腹盆 CT（增强）", "أشعة مقطعية للبطن والحوض بصبغة"],
 "76700": ["Ecografía abdominal completa", "Échographie abdominale complète", "全腹超声", "تصوير بالموجات فوق الصوتية للبطن"],
 "76805": ["Ecografía obstétrica tras el primer trimestre", "Échographie obstétricale après le 1er trimestre", "孕中期产科超声", "تصوير صوتي للحمل بعد الثلث الأول"],
 "76830": ["Ecografía transvaginal", "Échographie endovaginale", "经阴道超声", "تصوير صوتي عبر المهبل"],
 "77067": ["Mamografía de cribado bilateral", "Mammographie de dépistage bilatérale", "双侧乳腺筛查", "تصوير الثديين للكشف المبكر"],
 "065": ["Hemorragia o infarto cerebral, con complicaciones", "Hémorragie ou infarctus cérébral, avec complications", "脑出血或脑梗死（有并发症）", "نزيف أو احتشاء دماغي مع مضاعفات"],
 "066": ["Hemorragia o infarto cerebral, sin complicaciones", "Hémorragie ou infarctus cérébral, sans complications", "脑出血或脑梗死（无并发症）", "نزيف أو احتشاء دماغي دون مضاعفات"],
 "190": ["EPOC con complicaciones mayores", "BPCO avec complications majeures", "慢阻肺（严重并发症）", "انسداد رئوي مزمن مع مضاعفات كبرى"],
 "191": ["EPOC con complicaciones", "BPCO avec complications", "慢阻肺（有并发症）", "انسداد رئوي مزمن مع مضاعفات"],
 "193": ["Neumonía con complicaciones mayores", "Pneumonie avec complications majeures", "肺炎（严重并发症）", "التهاب رئة مع مضاعفات كبرى"],
 "194": ["Neumonía con complicaciones", "Pneumonie avec complications", "肺炎（有并发症）", "التهاب رئة مع مضاعفات"],
 "291": ["Insuficiencia cardíaca con complicaciones mayores", "Insuffisance cardiaque avec complications majeures", "心衰（严重并发症）", "قصور القلب مع مضاعفات كبرى"],
 "292": ["Insuficiencia cardíaca con complicaciones", "Insuffisance cardiaque avec complications", "心衰（有并发症）", "قصور القلب مع مضاعفات"],
 "871": ["Septicemia con complicaciones mayores", "Septicémie avec complications majeures", "败血症（严重并发症）", "إنتان الدم مع مضاعفات كبرى"],
 "872": ["Septicemia sin complicaciones mayores", "Septicémie sans complications majeures", "败血症（无严重并发症）", "إنتان الدم دون مضاعفات كبرى"],
 "787": ["Cesárea con complicaciones", "Césarienne avec complications", "剖孫产（有并发症）", "ولادة قيصرية مع مضاعفات"],
 "788": ["Cesárea sin complicaciones", "Césarienne sans complications", "剖孫产（无并发症）", "ولادة قيصرية دون مضاعفات"],
 "806": ["Parto vaginal con complicaciones", "Accouchement par voie basse avec complications", "阳道分娩（有并发症）", "ولادة طبيعية مع مضاعفات"],
 "807": ["Parto vaginal sin complicaciones", "Accouchement par voie basse sans complications", "阳道分娩（无并发症）", "ولادة طبيعية دون مضاعفات"],
 "469": ["Prótesis de cadera o rodilla con complicaciones", "Prothèse de hanche ou genou avec complications", "髀/膝关节置换（有并发症）", "استبدال مفصل الورك أو الركبة مع مضاعفات"],
 "470": ["Prótesis de cadera o rodilla sin complicaciones", "Prothèse de hanche ou genou sans complications", "髀/膝关节置换（无并发症）", "استبدال مفصل الورك أو الركبة دون مضاعفات"],
 "481": ["Cirugía de cadera y fémur con complicaciones", "Chirurgie de hanche et fémur avec complications", "髀部与股骨手术（有并发症）", "جراحة الورك وعظم الفخذ مع مضاعفات"],
 "483": ["Cirugía mayor de extremidad superior", "Chirurgie majeure du membre supérieur", "上肢大关节手术", "جراحة كبرى للطرف العلوي"],
 "80048": ["Panel metabólico básico", "Bilan métabolique de base", "基础代谢组合", "فحص استقلابي أساسي"],
 "80053": ["Panel metabólico completo", "Bilan métabolique complet", "全面代谢组合", "فحص استقلابي شامل"],
 "80061": ["Perfil lipídico", "Bilan lipidique", "血脂全套", "فحص الدهون"],
 "81001": ["Análisis de orina con microscopio", "Analyse d'urine avec examen microscopique", "尿常规及镳检", "تحليل بول مع الفحص المجهري"],
 "83036": ["Hemoglobina glicosilada (A1c)", "Hémoglobine glyquée (HbA1c)", "糖化血红蛋白 A1c", "الهيموغلوبين السكري A1c"],
 "84443": ["Hormona estimulante del tiroides (TSH)", "Thyréostimuline (TSH)", "甲状腺刺激素 TSH", "هرمون تحفيز الغدة الدرقية"],
 "85025": ["Hemograma completo con fórmula", "Hémogramme complet avec formule", "全血细胞计数及分类", "تعداد دم كامل مع الصيغة"],
 "86803": ["Anticuerpos de hepatitis C", "Anticorps de l'hépatite C", "丙肝抗体", "أجسام مضادة لالتهاب الكبد C"],
 "87086": ["Urocultivo", "Culture d'urine", "尿培养", "زرع البول"],
 "88305": ["Anatomía patológica, nivel IV", "Anatomopathologie, niveau IV", "外科病理 IV 级", "فحص نسيجي جراحي مستوى 4"],
 "59400": ["Parto vaginal, paquete completo", "Accouchement par voie basse, forfait global", "阳道分娩打包费用", "ولادة طبيعية – الباقة الكاملة"],
 "59510": ["Cesárea, paquete completo", "Césarienne, forfait global", "剖孫产打包费用", "ولادة قيصرية – الباقة الكاملة"],
 "62323": ["Inyección epidural lumbar con imagen", "Infiltration épidurale lombaire sous imagerie", "腰礎外注射（影像引导）", "حقنة فوق الجافية القطنية مع تصوير"],
 "64483": ["Inyección epidural transforaminal lumbar", "Infiltration transforaminale lombaire", "腰椎经椒间孔注射", "حقنة عبر الثقبة القطنية"],
 "90471": ["Administración de vacuna", "Administration d'un vaccin", "疫苗接种服务", "إعطاء التطعيم"],
 "90686": ["Vacuna antigripal tetravalente", "Vaccin antigrippal quadrivalent", "四价流感疫苗", "لقاح الإنفلونزا الرباعي"],
 "19120": ["Extirpación de lesión mamaria", "Exérèse d'une lésion du sein", "乳腺病变切除", "استئصال آفة في الثدي"],
 "20610": ["Artrocentesis de articulación mayor", "Ponction d'une grosse articulation", "大关节穿刺", "بزل مفصل كبير"],
 "27130": ["Prótesis total de cadera", "Prothèse totale de hanche", "全髀关节置换", "استبدال كامل لمفصل الورك"],
 "27447": ["Prótesis total de rodilla", "Prothèse totale du genou", "全膝关节置换", "استبدال كامل لمفصل الركبة"],
 "29826": ["Artroscopia de hombro con descompresión", "Arthroscopie d'épaule avec décompression", "肩关节镜减压术", "تنظير الكتف مع تخفيف الضغط"],
 "29881": ["Artroscopia de rodilla con meniscectomía", "Arthroscopie du genou avec méniscectomie", "膝关节镜半月板切除", "تنظير الركبة مع استئصال الغضروف"],
 "47562": ["Colecistectomía laparoscópica", "Cholécystectomie par cœlioscopie", "腹腔镜胆囊切除", "استئصال المرارة بالمنظار"],
 "49505": ["Reparación de hernia inguinal", "Cure de hernie inguinale", "腹股疝修补", "إصلاح الفتق الإربي"],
 "52000": ["Cistoscopia", "Cystoscopie", "膀胱镜检查", "تنظير المثانة"],
 "66984": ["Cirugía de cataratas con lente intraocular", "Chirurgie de la cataracte avec implant", "白内障手术及人工晶体", "إزالة المياه البيضاء مع عدسة"],
 "97110": ["Fisioterapia, ejercicio terapéutico", "Kinésithérapie, exercices thérapeutiques", "物理治疗运动训练", "علاج طبيعي – تمارين"],
 "97140": ["Terapia manual", "Thérapie manuelle", "手法治疗", "علاج يدوي"],
}


def pack(table):
    """{english: [es, fr, zh, ar]} -> {lang: {english: translation}}"""
    out = {l: {} for l in LANGS}
    for en, vals in table.items():
        if len(vals) != len(LANGS):
            raise SystemExit("wrong number of translations for: %r" % en)
        for i, l in enumerate(LANGS):
            out[l][en] = vals[i]
    return out


bundle = {"meta": META, "langs": LANGS}
for name, table in (("ui", UI), ("cat", CAT), ("catgroup", CATGROUP),
                    ("cond", COND), ("pop", POP), ("svc", SVC)):
    bundle[name] = pack(table)

out = os.path.join(ROOT, "web", "i18n.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(bundle, f, ensure_ascii=False, separators=(",", ":"))

print("languages: %s" % ", ".join(LANGS))
for name, table in (("ui", UI), ("cat", CAT), ("catgroup", CATGROUP),
                    ("cond", COND), ("pop", POP), ("svc", SVC)):
    print("  %-9s %3d strings x %d = %d" % (name, len(table), len(LANGS),
                                            len(table) * len(LANGS)))
print("%s: %.0f KB" % (out, os.path.getsize(out) / 1024))
