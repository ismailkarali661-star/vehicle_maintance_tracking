import sqlite3

DATABASE = 'vehicle_maintenance.db'

# ─── 1. Create table ─────────────────────────────────────────────────────────

CREATE_TABLE = '''
CREATE TABLE IF NOT EXISTS purchase_guide_notes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    brand         TEXT NOT NULL,
    model         TEXT NOT NULL,
    score         INTEGER NOT NULL DEFAULT 70,   -- 0-100 overall score
    reliability   INTEGER DEFAULT 70,            -- reliability
    comfort       INTEGER DEFAULT 70,            -- comfort
    performance   INTEGER DEFAULT 65,            -- performance
    economy       INTEGER DEFAULT 70,            -- economy (fuel + maintenance)
    verdict       TEXT NOT NULL DEFAULT 'good',  -- excellent|good|average|poor
    summary       TEXT,                          -- short summary (1-2 sentences)
    pros          TEXT,                          -- JSON array ["...", "..."]
    cons          TEXT,                          -- JSON array ["...", "..."]
    price_min     INTEGER,                       -- used car min price
    price_max     INTEGER,                       -- used car max price
    target_buyer  TEXT,                          -- target buyer profile
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

# ─── 2. Data ──────────────────────────────────────────────────────────────────

import json

NOTES = [
    # Toyota
    ('Toyota', 'Corolla', 88, 90, 80, 75, 88, 'excellent',
     'One of the best-selling models; stands out for high reliability and low maintenance costs.',
     json.dumps(['Engine failures extremely rare', 'Spare parts cheap and widely available', 'Balanced fuel consumption', 'Low depreciation']),
     json.dumps(['Interior quality below premium segment', 'Driving dynamics unremarkable', 'Sound insulation average']),
     450000, 950000, 'Those seeking an economical and reliable car, budget-conscious families'),

    ('Toyota', 'Yaris', 82, 88, 75, 70, 90, 'good',
     'Ideal for city use; small but sturdy and fuel-efficient.',
     json.dumps(['Excellent fuel economy', 'Easy in tight streets', 'Low maintenance cost']),
     json.dumps(['Small boot space', 'Tiring on long journeys', 'Rear seat cramped']),
     280000, 600000, 'City dwellers, singles or couples'),

    ('Toyota', 'RAV4', 85, 87, 82, 80, 78, 'good',
     'A long-lasting, spacious family SUV suited to both roads and mild off-road.',
     json.dumps(['High driving comfort', 'Large boot', 'Hybrid option available', 'Durability']),
     json.dumps(['Fuel consumption average for SUV class', 'Expensive for price-value ratio', 'Size awkward in cities']),
     700000, 1400000, 'Families looking for a vehicle for travel and outdoor activities'),

    ('Toyota', 'C-HR', 80, 82, 78, 72, 80, 'good',
     'Draws attention with its unconventional design; a reliable member of the urban SUV segment.',
     json.dumps(['Striking design', 'Solid mechanicals', 'Hybrid version fuel-efficient']),
     json.dumps(['Poor rear visibility', 'Rear headroom limited', 'Small boot']),
     450000, 850000, 'Young users who prioritise design'),

    ('Toyota', 'Hilux', 87, 92, 70, 82, 65, 'excellent',
     'A pick-up legendary for its legendary toughness in demanding conditions.',
     json.dumps(['Incredible durability', 'High towing capacity', 'Long lifespan']),
     json.dumps(['High fuel consumption', 'Difficult to use in the city', 'Plain interior']),
     850000, 1800000, 'Farmers, construction workers, off-road enthusiasts'),

    ('Toyota', 'Camry', 84, 88, 85, 75, 80, 'good',
     'Offers comfort and reliability together in the large sedan segment.',
     json.dumps(['Spacious interior', 'Low hybrid consumption', 'High safety score']),
     json.dumps(['Limited after-sales service network', 'Light steering feel', 'High price']),
     700000, 1300000, 'Upper-segment sedan seekers, long-distance drivers'),

    # Volkswagen
    ('Volkswagen', 'Golf', 82, 80, 85, 80, 72, 'good',
     'The reference model of the hatchback segment; stands out for driving dynamics and a quality cabin.',
     json.dumps(['High driving enjoyment', 'Good interior material quality', 'Wide engine choice']),
     json.dumps(['DSG gearbox issues possible', 'Maintenance cost higher than Toyota', 'Minor faults frequent']),
     400000, 850000, 'Driving enthusiasts, fans of European aesthetics'),

    ('Volkswagen', 'Polo', 78, 78, 80, 75, 75, 'good',
     'Quality B-segment hatchback; Golf\'s smaller sibling.',
     json.dumps(['Driving quality above segment average', 'Good interior materials', 'Balanced fuel economy']),
     json.dumps(['1.0 TSI may cause issues long-term', 'Small boot', 'Maintenance cost higher than Dacia']),
     300000, 650000, 'B-segment buyers who prioritise quality'),

    ('Volkswagen', 'Passat', 80, 80, 84, 78, 70, 'good',
     'Spacious and comfortable upper-segment sedan; ideal for long distances.',
     json.dumps(['Spacious interior', 'Top-level driving comfort', 'DSG versions quick']),
     json.dumps(['High maintenance cost', 'DSG problem potential', 'Average fuel consumption']),
     500000, 1100000, 'Long-distance professionals, large families'),

    ('Volkswagen', 'Tiguan', 81, 81, 83, 76, 71, 'good',
     'The premium alternative in the urban compact SUV class.',
     json.dumps(['Quality interior', 'Large boot', '4Motion AWD option']),
     json.dumps(['Maintenance and spare parts expensive', 'DSG gearbox risk', 'High repair costs when it breaks']),
     550000, 1200000, 'Premium SUV seekers, VW brand loyalists'),

    ('Volkswagen', 'T-Roc', 78, 78, 80, 74, 72, 'good',
     'Small SUV with sporty design; young and dynamic.',
     json.dumps(['Attractive design', 'Good driving dynamics', 'Rich tech features']),
     json.dumps(['Long-term questions about 1.0 TSI engine', 'Small boot', 'Rear seat cramped']),
     450000, 900000, 'Young and dynamic users'),

    # Renault
    ('Renault', 'Megane', 72, 70, 78, 72, 74, 'average',
     'A compact shaped by French design philosophy; comfortable but requires careful maintenance.',
     json.dumps(['High comfort', 'Good cabin technology', 'Balanced price-value']),
     json.dumps(['Electrical faults can occur', 'High maintenance sensitivity', 'Long-term reliability below VW']),
     280000, 650000, 'Comfort-first users'),

    ('Renault', 'Clio', 74, 72, 76, 70, 78, 'good',
     'Small hatchback that stands out for city manoeuvrability and comfort.',
     json.dumps(['Excellent in the city', 'Affordable price', 'Cabin comfort above segment']),
     json.dumps(['Electrical issue risk', 'Tiring on long journeys', 'Occasional faults with 1.0 TCe']),
     250000, 550000, 'City use, young users'),

    ('Renault', 'Taliant', 76, 74, 78, 72, 78, 'good',
     'Budget-friendly sedan produced for the local market; practical and affordable.',
     json.dumps(['Locally produced', 'Low maintenance cost', 'Large boot']),
     json.dumps(['Unremarkable driving dynamics', 'Basic interior materials', 'Limited engine power']),
     300000, 600000, 'Budget-friendly sedan seekers, taxi/rental fleets'),

    ('Renault', 'Duster', 77, 78, 72, 70, 80, 'good',
     'The most affordable option in the budget-friendly SUV segment.',
     json.dumps(['Good ground clearance', 'Affordable price', 'Simple and durable mechanicals']),
     json.dumps(['Low-quality interior materials', 'Poor noise insulation', 'Lacking technology']),
     350000, 750000, 'Economy SUV seekers, rural use'),

    # Ford
    ('Ford', 'Focus', 78, 76, 80, 76, 74, 'good',
     'A favourite hatchback alternative with a dynamic driving character.',
     json.dumps(['High driving enjoyment', 'Balanced pricing', 'Non-PowerShift models solid']),
     json.dumps(['PowerShift gearbox serious problem (2012-2018)', 'Maintenance requires attention', 'Electrical glitches']),
     280000, 600000, 'Driving enthusiasts — avoid PowerShift variants'),

    ('Ford', 'Kuga', 79, 78, 80, 76, 73, 'good',
     'Spacious and well-equipped compact SUV; stands out with its Hybrid version.',
     json.dumps(['Spacious cabin', 'Good hybrid fuel economy', 'Good driving comfort']),
     json.dumps(['Brake issue on some 1.5 EcoBoost models', 'Average maintenance cost', 'DCT risk']),
     500000, 1100000, 'Families and long-distance drivers'),

    ('Ford', 'Puma', 80, 78, 82, 76, 78, 'good',
     'Urban SUV combining modern design with an EcoBoost engine.',
     json.dumps(['Attractive design', 'Mild hybrid version economical', 'Under-boot storage compartment']),
     json.dumps(['Rear headroom limited', 'No independent rear suspension', 'Small boot']),
     450000, 950000, 'Young urban families'),

    ('Ford', 'Ranger', 85, 87, 72, 80, 65, 'good',
     'A reliable and powerful option in the work-oriented pick-up segment.',
     json.dumps(['Strong towing', 'Large load area', 'Good off-road capability']),
     json.dumps(['High fuel consumption', 'Difficult to manoeuvre in the city', 'Parking challenging']),
     750000, 1600000, 'Work use, farmers, construction workers'),

    # Honda
    ('Honda', 'Civic', 83, 84, 80, 78, 80, 'good',
     'A solid C-segment alternative balancing reliability and driving dynamics.',
     json.dumps(['Long-lasting engine', 'Balanced driving', 'Quality interior', 'Holds its value']),
     json.dumps(['CVT gearbox feels ordinary', 'Average fuel consumption', 'Air-con issues on some models']),
     380000, 850000, 'Reliability-first users'),

    ('Honda', 'CR-V', 82, 84, 78, 76, 76, 'good',
     'A solid choice for those wanting a spacious and reliable family SUV.',
     json.dumps(['Spacious interior', 'Good reliability', 'Hybrid economical']),
     json.dumps(['Price slightly high', 'CVT limits driving enjoyment', 'Understated exterior design']),
     650000, 1300000, 'Family SUV seekers'),

    # Hyundai
    ('Hyundai', 'i20', 76, 76, 75, 70, 80, 'good',
     'Preferred in the B-segment for its good equipment level and competitive price.',
     json.dumps(['Rich equipment', 'Modern design', 'Balanced fuel economy']),
     json.dumps(['1.0 T-GDI some faults reported', 'Faster depreciation than Toyota', 'Average interior materials']),
     280000, 580000, 'Young users, budget-conscious families'),

    ('Hyundai', 'Tucson', 82, 82, 82, 78, 76, 'good',
     'A strong compact SUV rival with striking design, comfort and features.',
     json.dumps(['Eye-catching design', 'Rich equipment', 'Good hybrid option']),
     json.dumps(['Maintenance cost above segment average', 'Long-term reliability uncertain', 'DCT risk']),
     550000, 1100000, 'Modern SUV seekers, tech enthusiasts'),

    ('Hyundai', 'IONIQ 5', 85, 82, 86, 88, 70, 'good',
     'Stands out in the EV segment with outstanding range and fast charging.',
     json.dumps(['800V fast charging', 'Spacious interior', 'Good range', 'V2L feature']),
     json.dumps(['High price', 'Charging infrastructure still developing', 'Range drops in cold weather']),
     950000, 1800000, 'EV switchers, technology enthusiasts'),

    # Kia
    ('Kia', 'Sportage', 83, 82, 83, 79, 76, 'good',
     'One of the strongest rivals in the compact SUV segment; interior space and safety stand out.',
     json.dumps(['Spacious interior', 'High safety score', 'Rich equipment', '5-year warranty']),
     json.dumps(['Average maintenance cost', 'Fuel consumption not outstanding', 'Hybrid price high']),
     550000, 1100000, 'Family use, safety-first choices'),

    ('Kia', 'EV6', 86, 84, 86, 88, 72, 'excellent',
     'Combines performance, range and design in the EV segment.',
     json.dumps(['800V charging infrastructure', 'Excellent performance', 'Spacious cabin', 'Award-winning design']),
     json.dumps(['High price', 'Rear camera quality insufficient', 'Firm suspension']),
     1050000, 1900000, 'Those seeking performance combined with electric driving'),

    ('Kia', 'Picanto', 72, 74, 70, 65, 83, 'good',
     'A practical solution for those who want a new car on the tightest budget.',
     json.dumps(['Low fuel consumption', 'Easy parking', 'Low tax', 'Cheap maintenance']),
     json.dumps(['Limited safety equipment', 'Very little engine power', 'Poor comfort outside the city']),
     220000, 480000, 'Minimal city use, budget-constrained buyers'),

    # Dacia
    ('Dacia', 'Sandero', 73, 72, 68, 65, 88, 'good',
     'Europe\'s cheapest new car; offers value through simplicity and low running costs.',
     json.dumps(['Very low purchase price', 'Lowest maintenance cost', 'Durable mechanicals']),
     json.dumps(['Plastic and plain interior', 'Poor noise insulation', 'Lacks technology']),
     280000, 580000, 'Budget as primary criterion, those wanting a simple car'),

    ('Dacia', 'Duster', 76, 78, 70, 68, 82, 'good',
     'The most economical SUV; simple but functional with off-road ability.',
     json.dumps(['Incredibly affordable', '4x4 option available', 'Simple mechanics = fewer faults']),
     json.dumps(['Low cabin quality', 'Ordinary driving comfort', 'Almost no technology']),
     350000, 750000, 'Budget SUV seekers, rural use'),

    ('Dacia', 'Spring', 70, 70, 65, 65, 90, 'average',
     'The cheapest electric car; sufficient for city use but with limited range.',
     json.dumps(['Cheapest EV', 'Low running cost', 'Adequate for city use']),
     json.dumps(['Very short range', 'Low engine power', 'Slow charging', 'Difficult outside the city']),
     450000, 750000, 'Those who only want EV use within the city'),

    # Skoda
    ('Skoda', 'Octavia', 84, 82, 85, 80, 76, 'good',
     'Delivers VW quality at a more accessible price; one of the most sensible sedan choices available.',
     json.dumps(['VW platform = quality', 'Spacious interior', 'Large boot', 'Good fuel economy']),
     json.dumps(['DSG risk (dual-clutch)', 'Maintenance close to VW pricing', 'Less well-known outside home market']),
     450000, 950000, 'Value-seeking C/D segment buyers'),

    ('Skoda', 'Karoq', 82, 80, 82, 78, 74, 'good',
     'A spacious and comfortable compact SUV option with Skoda\'s value-focused philosophy.',
     json.dumps(['Spacious interior', 'Adjustable boot floor', 'Quality materials']),
     json.dumps(['DSG may need attention', 'Spare parts at VW prices', 'Unremarkable driving dynamics']),
     500000, 1050000, 'Spacious, value-oriented SUV seekers'),

    # BMW
    ('BMW', '3 Series', 80, 75, 88, 88, 62, 'good',
     'The legendary driver-focused sedan; but maintenance costs are high.',
     json.dumps(['Unmatched driving enjoyment', 'Excellent engine performance', 'Prestige']),
     json.dumps(['Very high maintenance cost', 'N20 engine timing issue', 'Electrical problems', 'High fuel consumption']),
     600000, 1500000, 'Driving enjoyment as the top priority, those who can afford maintenance costs'),

    ('BMW', '5 Series', 79, 76, 88, 86, 58, 'good',
     'The pinnacle of upper-segment sedan comfort and performance; a maintenance budget is essential.',
     json.dumps(['Top-level comfort', 'Excellent driving', 'Rich technology']),
     json.dumps(['Very expensive maintenance', 'Shock absorbers wear quickly', 'Electronic faults', 'Expensive spare parts']),
     900000, 2000000, 'Upper income group, those willing to accept maintenance costs'),

    ('BMW', 'X3', 80, 78, 84, 82, 63, 'good',
     'A powerful representative of the premium compact SUV; must be bought with maintenance awareness.',
     json.dumps(['Superior interior quality', 'Good driving comfort', 'Solid AWD']),
     json.dumps(['High maintenance cost', 'B48 engine water pump issue', 'Shock absorbers may wear early']),
     800000, 1800000, 'Premium SUV seekers with a high maintenance budget'),

    # Mercedes-Benz
    ('Mercedes-Benz', 'C-Class', 79, 76, 88, 84, 60, 'good',
     'The symbol of comfort and prestige in the luxury sedan segment; requires careful selection.',
     json.dumps(['Excellent cabin quality', 'Rich safety equipment', 'High prestige']),
     json.dumps(['Very expensive maintenance', 'Electrical and electronic issues', '7G-DCT vibration problem', 'Fast depreciation']),
     700000, 1700000, 'Prestige and comfort seekers with a high maintenance budget'),

    ('Mercedes-Benz', 'GLC', 80, 78, 86, 84, 60, 'good',
     'Premium compact SUV balancing comfort and technology; maintenance costs must be considered.',
     json.dumps(['Exceptional comfort', 'Rich technology', 'Prestige', 'Spacious cabin']),
     json.dumps(['Very expensive maintenance', 'Very expensive spare parts', 'Shock absorbers may wear early', 'Minor faults frequent']),
     900000, 2200000, 'Upper-segment SUV seekers; high maintenance budget is mandatory'),

    # Audi
    ('Audi', 'A3', 78, 74, 84, 82, 63, 'good',
     'German quality and technology in the premium hatchback segment; maintenance costs must be factored in.',
     json.dumps(['Very good interior quality', 'Rich technology', 'S-Tronic delivers smooth driving']),
     json.dumps(['S-Tronic mechatronic issue', 'High maintenance cost', 'Carbon build-up on 1.4 TFSI']),
     500000, 1200000, 'Premium hatchback seekers, those wanting driving technology'),

    ('Audi', 'Q5', 81, 78, 85, 82, 62, 'good',
     'The pinnacle of technology and comfort in the premium compact SUV; a maintenance budget is essential.',
     json.dumps(['Excellent four-wheel drive system', 'Premium interior quality', 'Good driving comfort']),
     json.dumps(['Very high maintenance cost', 'Haldex issues', 'S-Tronic risk', 'Expensive spare parts']),
     850000, 1800000, 'Upper-segment SUV; high maintenance budget is mandatory'),

    # Peugeot
    ('Peugeot', '308', 72, 70, 78, 74, 73, 'average',
     'French design philosophy and driving comfort stand out; requires careful maintenance attention.',
     json.dumps(['Innovative cabin design', 'Good driving comfort', 'Nice steering feel']),
     json.dumps(['EGR issue (diesel)', 'VVT failure risk', 'Maintenance needs more attention', 'Long-term reliability weak']),
     280000, 620000, 'French brand enthusiasts, comfort-first buyers'),

    ('Peugeot', '3008', 75, 73, 80, 76, 72, 'good',
     'Stands out in the compact SUV class with its creative i-Cockpit cabin design.',
     json.dumps(['Unique i-Cockpit experience', 'Good comfort', 'Diesel version economical']),
     json.dumps(['Start/stop system problematic', 'EGR and DPF risk', 'Maintenance attention required']),
     450000, 980000, 'Those wanting a different design, comfort-first SUV'),

    # Opel
    ('Opel', 'Astra', 73, 72, 76, 74, 74, 'average',
     'Budget-friendly compact hatchback; reasonable equipment but choose carefully.',
     json.dumps(['Reasonable price', 'Good comfort', 'Adequate equipment']),
     json.dumps(['Electrical faults', 'Gearbox mount rubber wear', 'Average long-term reliability']),
     250000, 580000, 'Budget-conscious compact hatchback seekers'),

    ('Opel', 'Corsa', 70, 70, 72, 68, 75, 'average',
     'An economical B-segment option; simple and adequate but not premium.',
     json.dumps(['Affordable price', 'Easy in the city', 'Balanced fuel economy']),
     json.dumps(['Suspension noise can appear early', 'Plain interior quality', 'Lacking technology']),
     220000, 500000, 'Budget-constrained B-segment seekers'),

    # Fiat
    ('Fiat', 'Egea', 74, 72, 74, 70, 78, 'good',
     'An affordable sedan produced locally with the widest service network available.',
     json.dumps(['Local production', 'Cheap and widely available spare parts', 'Low maintenance cost', 'LPG version economical']),
     json.dumps(['Body noise', 'Gearbox noise (manual)', 'Plain interior quality']),
     280000, 600000, 'Those wanting a wide spare-parts and service network'),

    # Seat
    ('Seat', 'Leon', 79, 76, 82, 78, 72, 'good',
     'A sporty Spanish brand built on the VW platform; a Golf alternative.',
     json.dumps(['VW platform reliability', 'Sporty appearance', 'Varied engine choices']),
     json.dumps(['DSG gearbox risk', 'Less recognised at service centres', 'Spare parts at VW prices']),
     350000, 800000, 'Those seeking a sporty VW alternative'),

    # Tesla
    ('Tesla', 'Model 3', 87, 80, 88, 92, 75, 'excellent',
     'The technology leader of the electric sedan segment; service network growing.',
     json.dumps(['Technology leader', 'Outstanding performance', 'OTA updates', 'Wide charging network']),
     json.dumps(['Inconsistent panel gaps', 'Service network still limited', 'Requires specialist service', 'Range drops in cold weather']),
     1100000, 2200000, 'Early EV adopters, technology enthusiasts'),

    # Volvo
    ('Volvo', 'XC60', 83, 80, 88, 84, 65, 'good',
     'The pinnacle of safety and comfort; Scandinavian simplicity in a premium SUV.',
     json.dumps(['World-class safety', 'Top-level interior comfort', 'Elegant design']),
     json.dumps(['High maintenance cost', 'Some powertrain issues', 'Limited service network', 'Expensive spare parts']),
     900000, 2000000, 'Safety-first premium SUV seekers'),
]

# ─── 3. Apply ─────────────────────────────────────────────────────────────────

conn = sqlite3.connect(DATABASE)
cur = conn.cursor()

cur.executescript(CREATE_TABLE)

cur.execute('SELECT COUNT(*) FROM purchase_guide_notes').fetchone()
cur.execute('DELETE FROM purchase_guide_notes')  # start fresh

cur.executemany('''
    INSERT INTO purchase_guide_notes
        (brand, model, score, reliability, comfort, performance, economy,
         verdict, summary, pros, cons, price_min, price_max, target_buyer)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
''', NOTES)

conn.commit()

count = cur.execute('SELECT COUNT(*) FROM purchase_guide_notes').fetchone()[0]
print(f"✅ purchase_guide_notes table created: {count} records inserted.")

# Summary
for row in cur.execute('SELECT brand, model, score, verdict FROM purchase_guide_notes ORDER BY brand, model').fetchall():
    print(f"  {row[0]:20} {row[1]:15} score={row[2]}  verdict={row[3]}")

conn.close()