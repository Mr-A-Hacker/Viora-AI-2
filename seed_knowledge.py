"""
Seed knowledge base with comprehensive Wikipedia full-text articles.
Clears old entries and replaces with curated, full-text knowledge.
"""
import json
import logging
import math
import re
import sys
import time
from pathlib import Path
import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_knowledge")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from knowledge import save, rebuild_index, chunk_text

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "VioraAI-Seed/1.0 (knowledge seeder)"}
DELAY = 3.0

# ─── Curated article titles ──────────────────────────────────

HISTORY = [
    "History", "Ancient history", "Middle Ages", "Renaissance", "Age of Discovery",
    "Industrial Revolution", "French Revolution", "American Revolution",
    "World War I", "World War II", "Cold War", "Russian Revolution",
    "Great Depression", "Vietnam War", "Korean War", "American Civil War",
    "Ancient Egypt", "Mesopotamia", "Ancient Greece", "Ancient Rome",
    "Roman Empire", "Byzantine Empire", "Mongol Empire", "Ottoman Empire",
    "British Empire", "Spanish Empire", "Holy Roman Empire", "Persian Empire",
    "Mughal Empire", "Inca Empire", "Aztec Empire", "Maya civilization",
    "Indus Valley Civilisation", "Ancient China", "Qin dynasty", "Han dynasty",
    "Tang dynasty", "Ming dynasty", "Qing dynasty", "Silk Road",
    "Crusades", "Black Death", "Hundred Years' War", "Thirty Years' War",
    "Napoleonic Wars", "Seven Years' War", "Crimean War",
    "Alexander the Great", "Julius Caesar", "Genghis Khan", "Napoleon",
    "George Washington", "Abraham Lincoln", "Winston Churchill",
    "Mahatma Gandhi", "Martin Luther King Jr.", "Nelson Mandela",
    "Franklin D. Roosevelt", "Theodore Roosevelt", "Thomas Jefferson",
    "Leonardo da Vinci", "Galileo Galilei", "Isaac Newton", "Albert Einstein",
    "Charles Darwin", "Socrates", "Plato", "Aristotle", "Confucius",
    "Sigmund Freud", "Karl Marx", "Adam Smith", "Niccolò Machiavelli",
    "Decolonization", "Civil rights movement", "French colonial empire",
    "Dutch colonial empire", "Portuguese colonial empire",
    "History of Japan", "History of India", "History of China",
    "History of Russia", "History of the United States",
    "History of Germany", "History of France", "History of the United Kingdom",
    "History of Africa", "History of the Middle East", "History of Europe",
    "History of South America", "History of Australia",
    "Ancient Carthage", "Babylonia", "Assyria", "Hittites", "Sparta",
    "Athens", "Macedonia (ancient kingdom)", "Ptolemaic Kingdom",
    "Viking Age", "Norman conquest of England", "Magna Carta",
    "Hundred Years' War", "War of the Roses", "Spanish Inquisition",
    "Protestant Reformation", "Catholic Church", "Scientific Revolution",
    "Age of Enlightenment", "Colonialism", "Imperialism",
    "Atlantic slave trade", "Abolitionism", "Suffrage", "Women's suffrage",
    "Industrial Revolution in the United Kingdom",
    "Meiji Restoration", "Russian Empire", "Soviet Union",
    "Nazi Germany", "The Holocaust", "Atomic bombings of Hiroshima and Nagasaki",
    "Manhattan Project", "Marshall Plan", "Berlin Wall",
    "Space Race", "Apollo program", "Cuban Missile Crisis",
    "Chinese Communist Revolution", "Mao Zedong", "Joseph Stalin",
    "Adolf Hitler", "Benito Mussolini", "Franklin D. Roosevelt",
    "Harry S. Truman", "Dwight D. Eisenhower", "John F. Kennedy",
    "Richard Nixon", "Ronald Reagan", "Margaret Thatcher",
    "Slavery", "Feudalism", "Capitalism", "Socialism", "Communism",
    "Fascism", "Democracy", "Monarchy", "Republic",
    "United Nations", "League of Nations", "European Union",
    "Gospel", "History of Christianity", "History of Islam",
    "History of Buddhism", "History of Judaism",
    "Renaissance art", "Renaissance music", "Baroque", "Romanticism",
    "Age of sail", "Piracy", "Gold rush",
    "Holodomor", "Armenian genocide", "Cambodian genocide",
    "Apartheid", "Jim Crow laws", "Segregation",
    "September 11 attacks", "War on terror",
    "French Indochina", "Scramble for Africa",
    "Boxer Rebellion", "Opium Wars", "Taiping Rebellion",
    "American Revolution", "War of 1812", "Mexican–American War",
    "Spanish–American War", "Philippine–American War",
    "Battle of Waterloo", "Battle of Gettysburg", "Battle of Stalingrad",
    "D-Day", "Pearl Harbor attack",
    "Fall of the Western Roman Empire", "Fall of Constantinople",
    "Boston Tea Party", "Declaration of Independence",
    "US Constitution", "Bill of Rights",
    "Encomienda", "Columbian exchange", "Age of Discovery",
    "Marco Polo", "Christopher Columbus", "Ferdinand Magellan",
    "Vasco da Gama", "Hernán Cortés", "Francisco Pizarro",
]

GEOGRAPHY = [
    "Geography", "Continent", "Ocean", "Mountain", "River", "Desert",
    "Africa", "Asia", "Europe", "North America", "South America",
    "Australia (continent)", "Antarctica",
    "Atlantic Ocean", "Pacific Ocean", "Indian Ocean", "Arctic Ocean",
    "Himalayas", "Andes", "Alps", "Rocky Mountains", "Mount Everest",
    "Amazon River", "Nile", "Mississippi River", "Yangtze",
    "Ganges", "Danube", "Rhine", "Volga", "Amazon rainforest",
    "Sahara", "Gobi Desert", "Atacama Desert", "Arabian Desert",
    "Great Lakes", "Caspian Sea", "Dead Sea", "Lake Victoria",
    "Mediterranean Sea", "Caribbean", "South China Sea",
    "Tokyo", "London", "Paris", "Beijing", "New York City",
    "Mumbai", "Shanghai", "Delhi", "Cairo", "Moscow",
    "Istanbul", "Rome", "Berlin", "Madrid", "Bangkok",
    "Sydney", "Rio de Janeiro", "Mexico City", "Dubai", "Singapore",
    "Arctic", "Antarctic", "Greenland", "Central America",
    "Middle East", "Southeast Asia", "South Asia", "East Asia",
    "Western Europe", "Eastern Europe", "Scandinavia", "Balkans",
    "Suez Canal", "Panama Canal", "Strait of Gibraltar",
    "Ring of Fire", "Tectonic plate", "Plate tectonics",
    "Climate", "Tropical rainforest climate", "Desert climate",
    "Tundra", "Taiga", "Grassland", "Savanna",
    "Monsoon", "El Niño", "Gulf Stream",
    "Population", "World population", "Urbanization",
    "List of countries and dependencies by population",
    "List of countries and dependencies by area",
    "List of countries by GDP (nominal)",
    "European Union", "United Nations", "NATO",
]

SCIENCE = [
    "Science", "Scientific method", "Hypothesis", "Theory", "Law (science)",
    "Physics", "Classical mechanics", "Newton's laws of motion",
    "Thermodynamics", "Laws of thermodynamics", "Electromagnetism",
    "Special relativity", "General relativity", "Quantum mechanics",
    "Standard Model", "Particle physics", "Nuclear physics",
    "Atomic theory", "Wave–particle duality", "Schrödinger equation",
    "Quantum entanglement", "Uncertainty principle", "String theory",
    "Dark matter", "Dark energy", "Antimatter", "Black hole",
    "Neutron star", "Supernova", "Nuclear fusion", "Nuclear fission",
    "Speed of light", "Gravity", "Electromagnetic radiation",
    "Light", "Sound", "Energy", "Matter", "Mass",
    "Force", "Momentum", "Velocity", "Acceleration", "Friction",
    "Pressure", "Density", "Temperature", "Entropy", "Time",
    "Chemistry", "Periodic table", "Chemical element", "Chemical bond",
    "Chemical reaction", "Acid", "Base (chemistry)", "pH",
    "Oxidation", "Redox", "Catalysis", "Enzyme",
    "Organic chemistry", "Inorganic chemistry", "Analytical chemistry",
    "Polymer", "Protein", "Carbohydrate", "Lipid", "Nucleic acid",
    "Amino acid", "DNA", "RNA", "Cellular respiration",
    "Photosynthesis", "Mitosis", "Meiosis",
    "Biochemistry", "Molecular biology", "Cell biology",
    "Genetics", "Gene", "Chromosome", "Genome", "Evolution",
    "Natural selection", "Mutation", "Speciation",
    "Biology", "Life", "Organism", "Cell (biology)",
    "Eukaryote", "Prokaryote", "Virus", "Bacteria",
    "Plant", "Animal", "Fungus", "Protist",
    "Human", "Human body", "Human evolution",
    "Anatomy", "Physiology", "Neuroscience",
    "Brain", "Heart", "Lung", "Liver", "Kidney", "Skin",
    "Immune system", "Nervous system", "Circulatory system",
    "Respiratory system", "Digestive system", "Endocrine system",
    "Skeletal system", "Muscular system",
    "Ecosystem", "Biodiversity", "Extinction", "Endangered species",
    "Food chain", "Symbiosis", "Predation",
    "Botany", "Zoology", "Ecology", "Microbiology",
    "Astronomy", "Astrophysics", "Cosmology",
    "Solar System", "Sun", "Earth", "Moon", "Planet",
    "Mercury (planet)", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto",
    "Star", "Galaxy", "Milky Way", "Andromeda Galaxy",
    "Big Bang", "Cosmic microwave background",
    "Hubble's law", "Redshift", "Nebula", "Comet", "Asteroid",
    "Exoplanet", "Search for extraterrestrial intelligence",
    "Earth science", "Geology", "Meteorology", "Oceanography",
    "Mineral", "Rock (geology)", "Igneous rock", "Sedimentary rock",
    "Metamorphic rock", "Fossil", "Geological time scale",
    "Volcano", "Earthquake", "Tsunami", "Weathering",
    "Erosion", "Continental drift", "Plate tectonics",
    "Climate change", "Greenhouse effect", "Global warming",
    "Carbon cycle", "Water cycle", "Nitrogen cycle",
    "Marie Curie", "Richard Feynman", "Niels Bohr",
    "Erwin Schrödinger", "Werner Heisenberg", "Max Planck",
    "Michael Faraday", "James Clerk Maxwell", "Nikola Tesla",
    "Dmitri Mendeleev", "Linus Pauling", "Rosalind Franklin",
    "Gregor Mendel", "James Watson", "Francis Crick",
    "Carl Linnaeus", "Alfred Russel Wallace", "Stephen Hawking",
    "Louis Pasteur", "Robert Koch", "Alexander Fleming",
    "Alan Turing", "John von Neumann", "Gottfried Wilhelm Leibniz",
]

TECHNOLOGY = [
    "Technology", "Invention", "Innovation",
    "Computer", "Computer science", "Programming language",
    "Algorithm", "Data structure", "Software engineering",
    "Operating system", "Compiler", "Interpreter (computing)",
    "Computer programming", "Software", "Hardware",
    "Central processing unit", "Graphics processing unit",
    "Memory (computing)", "Computer data storage",
    "Transistor", "Integrated circuit", "Microprocessor",
    "Semiconductor", "Moore's law",
    "Internet", "World Wide Web", "Web browser", "HTTP",
    "HTML", "CSS", "JavaScript", "Python (programming language)",
    "Java (programming language)", "C (programming language)",
    "C++", "SQL", "Rust (programming language)",
    "Artificial intelligence", "Machine learning",
    "Deep learning", "Neural network", "Natural language processing",
    "Computer vision", "Reinforcement learning",
    "Large language model", "Transformer (deep learning architecture)",
    "GPT (language model)", "BERT (language model)",
    "Robotics", "Automation", "Cybernetics",
    "Database", "Relational database", "NoSQL",
    "Cloud computing", "Edge computing", "Distributed computing",
    "Cryptography", "Encryption", "Blockchain",
    "Computer network", "TCP/IP", "DNS", "IP address",
    "Wi-Fi", "Bluetooth", "LTE (telecommunication)", "5G",
    "Information theory", "Claude Shannon",
    "World Wide Web", "Tim Berners-Lee",
    "Google", "Apple Inc.", "Microsoft", "Amazon (company)",
    "Meta Platforms", "Nvidia", "Tesla, Inc.",
    "SpaceX", "Linux", "Unix", "Android (operating system)",
    "iOS", "Windows", "macOS",
    "Open-source software", "Free software",
    "Electricity", "Electric generator", "Electric motor",
    "Battery (electricity)", "Solar panel", "Wind turbine",
    "Nuclear power", "Renewable energy", "Fossil fuel",
    "Telecommunications", "Radio", "Television", "Satellite",
    "Telephone", "Smartphone", "Digital camera",
    "Printing press", "Steam engine", "Internal combustion engine",
    "Wheel", "Lever", "Pulley", "Inclined plane",
    "Laser", "LED", "LCD", "OLED",
    "Quantum computing", "Supercomputer",
    "Computer security", "Hacker (computer security)",
    "Graphical user interface", "Touchscreen",
    "Virtual reality", "Augmented reality",
    "3D printing", "Nanotechnology", "Biotechnology",
    "Genetic engineering", "CRISPR gene editing",
    "Spaceflight", "Rocket", "Satellite",
    "International Space Station", "Hubble Space Telescope",
    "James Webb Space Telescope",
    "Airplane", "Automobile", "Train", "Ship", "Submarine",
    "Radio telescope", "Particle accelerator",
    "Large Hadron Collider", "CERN",
    "Ada Lovelace", "Grace Hopper", "Linus Torvalds",
    "Steve Jobs", "Bill Gates", "Elon Musk", "Jeff Bezos",
    "Alan Turing", "Dennis Ritchie", "Ken Thompson",
    "Vint Cerf", "Robert Kahn", "Mark Zuckerberg",
]

CULTURE = [
    "Culture", "Art", "Music", "Literature", "Theatre", "Dance",
    "Painting", "Sculpture", "Architecture", "Photography",
    "Cinema", "Animation", "Comics",
    "Renaissance art", "Baroque", "Rococo", "Neoclassicism",
    "Romanticism", "Realism (art movement)", "Impressionism",
    "Post-Impressionism", "Cubism", "Surrealism", "Abstract art",
    "Pop art", "Modern art", "Contemporary art",
    "Classical music", "Jazz", "Blues", "Rock music", "Pop music",
    "Hip hop", "Electronic music", "Country music", "Reggae",
    "Music of Africa", "Music of India", "Music of China",
    "Symphony", "Opera", "Ballet", "Orchestra",
    "Ludwig van Beethoven", "Wolfgang Amadeus Mozart",
    "Johann Sebastian Bach", "Pyotr Ilyich Tchaikovsky",
    "The Beatles", "Elvis Presley", "Michael Jackson",
    "Bob Dylan", "Miles Davis", "Aretha Franklin",
    "William Shakespeare", "Homer", "Dante Alighieri",
    "Leo Tolstoy", "Fyodor Dostoevsky", "Jane Austen",
    "Charles Dickens", "Ernest Hemingway", "George Orwell",
    "Harper Lee", "Gabriel García Márquez",
    "Mark Twain", "Virginia Woolf", "James Joyce",
    "Franz Kafka", "J. R. R. Tolkien", "George R. R. Martin",
    "Novel", "Poetry", "Tragedy", "Comedy", "Fiction", "Non-fiction",
    "Mythology", "Folklore", "Fairy tale",
    "Greek mythology", "Norse mythology", "Hindu mythology",
    "Film", "History of film", "Hollywood (film industry)",
    "Bollywood", "Documentary film", "Animated film",
    "Steven Spielberg", "Alfred Hitchcock", "Stanley Kubrick",
    "Akira Kurosawa", "Charlie Chaplin", "Walt Disney",
    "Religion", "Christianity", "Islam", "Hinduism", "Buddhism",
    "Judaism", "Sikhism", "Jainism", "Zoroastrianism",
    "Shinto", "Taoism", "Confucianism", "Atheism", "Agnosticism",
    "Bible", "Quran", "Torah", "Vedas",
    "Jesus", "Muhammad", "Buddha", "Moses", "Abraham",
    "Philosophy", "Western philosophy", "Eastern philosophy",
    "Metaphysics", "Epistemology", "Ethics", "Logic", "Aesthetics",
    "Stoicism", "Existentialism", "Nihilism", "Utilitarianism",
    "Empiricism", "Rationalism", "Idealism", "Materialism",
    "Socrates", "Plato", "Aristotle", "René Descartes",
    "Immanuel Kant", "Friedrich Nietzsche", "John Stuart Mill",
    "David Hume", "Jean-Paul Sartre", "Simone de Beauvoir",
    "Ludwig Wittgenstein", "Bertrand Russell",
    "Language", "Linguistics", "Grammar", "Phonetics",
    "English language", "Mandarin Chinese", "Spanish language",
    "Arabic", "Hindi", "French language", "German language",
    "Japanese language", "Russian language", "Portuguese language",
    "Writing system", "Alphabet", "Chinese characters",
    "Library", "Book", "Manuscript",
    "Education", "University", "School",
    "Sports", "Olympic Games", "Football (soccer)", "Basketball",
    "Baseball", "Tennis", "Cricket", "Golf", "Boxing",
    "Martial arts", "Swimming (sport)", "Athletics (sport)",
    "Chess", "Video game", "History of video games",
    "Cuisine", "Food", "Cooking", "Wine", "Beer",
    "Fashion", "Clothing", "Textile",
    "Festival", "Holiday", "New Year",
    "Wedding", "Funeral", "Marriage", "Family",
    "UNESCO", "World Heritage Site",
    "Cultural globalization", "Pop culture",
    "Social media", "Mass media", "Journalism",
    "Museum", "Art gallery", "Concert",
]

POLITICS = [
    "Politics", "Government", "State (polity)", "Sovereignty",
    "Democracy", "Republic", "Monarchy", "Dictatorship",
    "Authoritarianism", "Totalitarianism", "Oligarchy",
    "Constitution", "Separation of powers",
    "Executive (government)", "Legislature", "Judiciary",
    "President (government title)", "Prime minister", "Cabinet (government)",
    "Parliament", "Congress", "Senate", "House of Commons",
    "Political party", "Election", "Voting", "Suffrage",
    "Law", "Criminal law", "Civil law (legal system)", "Common law",
    "International law", "Human rights", "Civil rights",
    "Constitutional law", "Contract", "Tort", "Property law",
    "Supreme Court", "Judge", "Jury", "Trial", "Appeal",
    "United Nations", "Security Council", "General Assembly",
    "European Union", "NATO", "World Trade Organization",
    "International Criminal Court", "World Health Organization",
    "International Monetary Fund", "World Bank",
    "African Union", "ASEAN", "Arab League",
    "Diplomacy", "Treaty", "Alliance", "Sanctions (law)",
    "War", "Military", "Army", "Navy", "Air force",
    "Nuclear weapon", "Chemical weapon", "Biological weapon",
    "Arms control", "Disarmament",
    "Terrorism", "Counter-terrorism",
    "Political ideology", "Conservatism", "Liberalism",
    "Socialism", "Communism", "Fascism", "Anarchism",
    "Nationalism", "Patriotism", "Populism",
    "Capitalism", "Free market", "Trade",
    "Globalization", "International relations",
    "Foreign policy", "Soft power", "Hard power",
    "Propaganda", "Censorship", "Freedom of speech",
    "Press freedom", "Internet censorship",
    "Public administration", "Bureaucracy",
    "Tax", "Budget", "Public policy",
    "Welfare state", "Social security", "Universal health care",
    "Citizenship", "Immigration", "Naturalization",
    "Colonialism", "Imperialism", "Decolonization",
    "Geopolitics", "Cold War", "Proxy war",
    "Indigenous rights", "Minority rights", "LGBT rights",
    "Feminism", "Gender equality", "Racial equality",
    "Environmental policy", "Climate change policy",
    "Political corruption", "Lobbying",
    "Think tank", "Non-governmental organization",
]

ECONOMICS = [
    "Economics", "Microeconomics", "Macroeconomics",
    "Supply and demand", "Market (economics)", "Price",
    "Competition (economics)", "Monopoly", "Oligopoly",
    "Inflation", "Deflation", "Recession", "Depression (economics)",
    "Gross domestic product", "Gross national product",
    "Unemployment", "Employment", "Labor market",
    "Money", "Currency", "Central bank", "Interest rate",
    "Bank", "Stock market", "Bond (finance)", "Dividend",
    "Investment", "Saving", "Wealth", "Poverty",
    "Income", "Wage", "Salary", "Profit (economics)",
    "Taxation", "Progressive tax", "Flat tax", "Value-added tax",
    "International trade", "Tariff", "Free trade", "Protectionism",
    "Globalization", "Outsourcing",
    "Economic inequality", "Gini coefficient",
    "Economic growth", "Development economics",
    "Capital (economics)", "Labor (economics)", "Productivity",
    "Keynesian economics", "Monetarism", "Classical economics",
    "Behavioral economics", "Game theory",
    "Mercantilism", "Capitalism", "Socialism",
    "Market economy", "Planned economy", "Mixed economy",
    "Industrial policy", "Privatization", "Nationalization",
    "Consumer", "Producer", "Entrepreneurship",
    "Insurance", "Risk management", "Diversification (finance)",
    "Real estate", "Mortgage loan", "Credit (finance)",
    "Crypto currency", "Bitcoin", "Blockchain",
    "World Bank", "International Monetary Fund",
    "World Trade Organization", "G20",
    "Asian Infrastructure Investment Bank",
    "European Central Bank", "Federal Reserve",
    "Dow Jones Industrial Average", "S&P 500",
    "NASDAQ", "New York Stock Exchange",
    "Economic history", "Great Depression", "Financial crisis of 2007–2008",
    "Hyperinflation", "Tulip mania", "South Sea Company",
    "Dutch East India Company", "British East India Company",
    "Hudson's Bay Company", "Gold standard",
    "Bretton Woods system", "Petrodollar recycling",
]

HEALTH = [
    "Health", "Medicine", "Disease", "Infection", "Injury",
    "Cancer", "Diabetes", "Cardiovascular disease", "Stroke",
    "Alzheimer's disease", "Parkinson's disease", "Epilepsy",
    "COVID-19", "HIV/AIDS", "Malaria", "Tuberculosis",
    "Pneumonia", "Influenza", "Hepatitis", "Cholera",
    "Ebola", "Zika fever", "Dengue fever",
    "Common cold", "Asthma", "Allergy", "Autoimmune disease",
    "Hypertension", "Obesity", "Malnutrition", "Anemia",
    "Mental disorder", "Depression (mood)", "Anxiety disorder",
    "Schizophrenia", "Bipolar disorder", "Post-traumatic stress disorder",
    "Attention deficit hyperactivity disorder",
    "Autism spectrum", "Obsessive–compulsive disorder",
    "Vaccine", "Antibiotic", "Antiviral drug", "Chemotherapy",
    "Surgery", "Anesthesia", "Transplantation", "Dialysis",
    "Diagnosis", "Medical imaging", "X-ray", "MRI", "CT scan",
    "Ultrasound", "ECG", "EEG",
    "Pharmacology", "Drug", "Pharmaceutical industry",
    "Gene therapy", "Stem cell", "Cloning",
    "First aid", "Cardiopulmonary resuscitation",
    "Public health", "Epidemiology", "Sanitation", "Hygiene",
    "Nutrition", "Diet (nutrition)", "Vitamin", "Mineral (nutrient)",
    "Exercise", "Sleep", "Stress (biology)",
    "Human anatomy", "Heart", "Brain", "Lungs", "Liver",
    "Kidney", "Stomach", "Intestine", "Eye", "Ear",
    "Bone", "Muscle", "Skin", "Blood", "Lymphatic system",
    "Reproductive system", "Pregnancy", "Childbirth",
    "Dentistry", "Optometry", "Psychiatry", "Pediatrics",
    "Cardiology", "Neurology", "Oncology", "Radiology",
    "Emergency medicine", "Intensive care medicine",
    "Nursing", "Midwifery", "Pharmacy", "Physical therapy",
    "Alternative medicine", "Traditional Chinese medicine",
    "Ayurveda", "Homeopathy", "Herbal medicine",
    "World Health Organization", "Red Cross", "Doctors Without Borders",
    "Medication", "Prescription drug", "Over-the-counter drug",
    "Side effect", "Addiction", "Substance abuse",
    "Smoking", "Alcohol (drug)", "Caffeine",
    "Life expectancy", "Infant mortality", "Maternal death",
    "Pandemic", "Epidemic", "Quarantine", "Vaccination",
    "Florence Nightingale", "Hippocrates", "Galen",
    "Edward Jenner", "Jonas Salk", "Joseph Lister",
]

MATH = [
    "Mathematics", "Arithmetic", "Algebra", "Geometry", "Trigonometry",
    "Calculus", "Statistics", "Probability", "Number theory",
    "Linear algebra", "Abstract algebra", "Topology",
    "Analysis (mathematics)", "Differential equation",
    "Set theory", "Logic", "Category theory",
    "Number", "Integer", "Rational number", "Real number",
    "Complex number", "Prime number", "Infinity",
    "Function (mathematics)", "Limit (mathematics)",
    "Derivative", "Integral", "Series (mathematics)",
    "Matrix (mathematics)", "Vector space", "Eigenvalues and eigenvectors",
    "Graph theory", "Combinatorics", "Discrete mathematics",
    "Fractal", "Chaos theory", "Complex system",
    "Pythagorean theorem", "Fibonacci sequence", "Golden ratio",
    "Pi", "E (mathematical constant)", "Logarithm",
    "Euclidean geometry", "Non-Euclidean geometry",
    "Trigonometric functions", "Fourier transform",
    "Probability distribution", "Normal distribution",
    "Bayesian inference", "Regression analysis",
    "Game theory", "Decision theory", "Information theory",
    "Algorithm", "Computational complexity theory",
    "Euclid", "Pythagoras", "Archimedes",
    "Leonhard Euler", "Carl Friedrich Gauss", "Bernhard Riemann",
    "Henri Poincaré", "David Hilbert", "John von Neumann",
    "Alan Turing", "Kurt Gödel", "Évariste Galois",
    "Srinivasa Ramanujan", "John Nash", "Ada Lovelace",
    "George Boole", "Gottlob Frege", "Bertrand Russell",
    "Andrey Kolmogorov", "Paul Erdős", "Alexander Grothendieck",
]

PHILOSOPHY = [
    "Philosophy", "Western philosophy", "Eastern philosophy",
    "Metaphysics", "Epistemology", "Ethics", "Logic", "Aesthetics",
    "Political philosophy", "Philosophy of mind",
    "Philosophy of science", "Philosophy of language",
    "Philosophy of religion", "Philosophy of mathematics",
    "Stoicism", "Epicureanism", "Cynicism (philosophy)",
    "Scholasticism", "Humanism", "Rationalism",
    "Empiricism", "Idealism", "Materialism", "Realism (philosophy)",
    "Pragmatism", "Existentialism", "Phenomenology",
    "Analytic philosophy", "Continental philosophy",
    "Utilitarianism", "Deontology", "Virtue ethics",
    "Nihilism", "Absurdism", "Relativism",
    "Determinism", "Free will", "Fatalism",
    "Solipsism", "Skepticism", "Dualism (philosophy of mind)",
    "Monism", "Pluralism (philosophy)",
    "Causality", "Consciousness", "Perception", "Knowledge",
    "Truth", "Reality", "Existence", "Meaning of life",
    "Good and evil", "Justice", "Rights", "Liberty",
    "Equality (social)", "Fairness", "Toleration",
    "Socrates", "Plato", "Aristotle",
    "René Descartes", "John Locke", "David Hume",
    "Immanuel Kant", "Georg Wilhelm Friedrich Hegel",
    "Arthur Schopenhauer", "Friedrich Nietzsche",
    "Søren Kierkegaard", "Jean-Paul Sartre",
    "Simone de Beauvoir", "Albert Camus",
    "Ludwig Wittgenstein", "Martin Heidegger",
    "Michel Foucault", "Noam Chomsky",
    "John Rawls", "Robert Nozick",
    "Thomas Aquinas", "Augustine of Hippo",
    "Karl Popper", "Thomas Kuhn",
    "Confucius", "Laozi", "Zhuang Zhou",
    "Buddhist philosophy", "Hindu philosophy",
    "Islamic philosophy", "Jewish philosophy",
]

PSYCHOLOGY = [
    "Psychology", "Clinical psychology", "Cognitive psychology",
    "Developmental psychology", "Social psychology",
    "Behavioral psychology", "Neuropsychology",
    "Personality psychology", "Abnormal psychology",
    "Psychiatry", "Psychotherapy", "Psychoanalysis",
    "Behaviorism", "Cognitivism (psychology)", "Humanistic psychology",
    "Gestalt psychology", "Evolutionary psychology",
    "Positive psychology", "Transpersonal psychology",
    "Memory", "Learning", "Perception", "Attention",
    "Cognition", "Intelligence", "Emotion", "Motivation",
    "Personality", "Consciousness", "Unconscious mind",
    "Dream", "Sleep", "Hypnosis", "Meditation",
    "Classical conditioning", "Operant conditioning",
    "Cognitive behavioral therapy", "Exposure therapy",
    "Nature versus nurture", "Attachment theory",
    "Cognitive development", "Moral development",
    "Id, ego and superego", "Oedipus complex",
    "Maslow's hierarchy of needs", "Self-actualization",
    "Sigmund Freud", "Carl Jung", "B. F. Skinner",
    "Jean Piaget", "Ivan Pavlov", "Abraham Maslow",
    "Carl Rogers", "Viktor Frankl", "Erik Erikson",
    "Lev Vygotsky", "John B. Watson", "Wilhelm Wundt",
    "Stanford prison experiment", "Milgram experiment",
    "Bystander effect", "Stockholm syndrome",
    "Placebo", "Nocebo",
]

ALL_TITLES = sum([
    HISTORY, GEOGRAPHY, SCIENCE, TECHNOLOGY, CULTURE,
    POLITICS, ECONOMICS, HEALTH, MATH, PHILOSOPHY, PSYCHOLOGY
], [])

# Country data for programmatic entries
COUNTRIES = [
    ("Afghanistan", "Kabul", "38,928,000", "652,860", "Pashto, Dari"),
    ("Albania", "Tirana", "2,877,000", "28,748", "Albanian"),
    ("Algeria", "Algiers", "44,700,000", "2,381,741", "Arabic, Berber"),
    ("Argentina", "Buenos Aires", "45,810,000", "2,780,400", "Spanish"),
    ("Armenia", "Yerevan", "2,963,000", "29,743", "Armenian"),
    ("Australia", "Canberra", "26,000,000", "7,692,024", "English"),
    ("Austria", "Vienna", "9,067,000", "83,879", "German"),
    ("Azerbaijan", "Baku", "10,353,000", "86,600", "Azerbaijani"),
    ("Bahrain", "Manama", "1,501,000", "786", "Arabic"),
    ("Bangladesh", "Dhaka", "169,800,000", "147,570", "Bengali"),
    ("Belarus", "Minsk", "9,255,000", "207,595", "Belarusian, Russian"),
    ("Belgium", "Brussels", "11,611,000", "30,689", "Dutch, French, German"),
    ("Bhutan", "Thimphu", "779,000", "38,394", "Dzongkha"),
    ("Bolivia", "Sucre", "12,080,000", "1,098,581", "Spanish, Quechua, Aymara"),
    ("Brazil", "Brasília", "215,000,000", "8,515,767", "Portuguese"),
    ("Bulgaria", "Sofia", "6,875,000", "110,994", "Bulgarian"),
    ("Cambodia", "Phnom Penh", "16,590,000", "181,035", "Khmer"),
    ("Canada", "Ottawa", "38,250,000", "9,984,670", "English, French"),
    ("Chile", "Santiago", "19,490,000", "756,096", "Spanish"),
    ("China", "Beijing", "1,412,000,000", "9,596,961", "Mandarin"),
    ("Colombia", "Bogotá", "51,050,000", "1,141,748", "Spanish"),
    ("Costa Rica", "San José", "5,180,000", "51,100", "Spanish"),
    ("Croatia", "Zagreb", "4,030,000", "56,594", "Croatian"),
    ("Cuba", "Havana", "11,240,000", "109,884", "Spanish"),
    ("Cyprus", "Nicosia", "1,260,000", "9,251", "Greek, Turkish"),
    ("Czech Republic", "Prague", "10,830,000", "78,866", "Czech"),
    ("Denmark", "Copenhagen", "5,910,000", "43,094", "Danish"),
    ("Dominican Republic", "Santo Domingo", "10,850,000", "48,671", "Spanish"),
    ("Ecuador", "Quito", "17,800,000", "283,560", "Spanish"),
    ("Egypt", "Cairo", "110,000,000", "1,002,450", "Arabic"),
    ("El Salvador", "San Salvador", "6,290,000", "21,041", "Spanish"),
    ("Estonia", "Tallinn", "1,350,000", "45,339", "Estonian"),
    ("Ethiopia", "Addis Ababa", "126,000,000", "1,104,300", "Amharic"),
    ("Finland", "Helsinki", "5,545,000", "338,424", "Finnish, Swedish"),
    ("France", "Paris", "67,800,000", "640,679", "French"),
    ("Georgia", "Tbilisi", "3,715,000", "69,700", "Georgian"),
    ("Germany", "Berlin", "83,200,000", "357,114", "German"),
    ("Ghana", "Accra", "33,480,000", "238,533", "English"),
    ("Greece", "Athens", "10,340,000", "131,957", "Greek"),
    ("Guatemala", "Guatemala City", "17,110,000", "108,889", "Spanish"),
    ("Haiti", "Port-au-Prince", "11,580,000", "27,750", "French, Haitian Creole"),
    ("Honduras", "Tegucigalpa", "10,290,000", "112,492", "Spanish"),
    ("Hungary", "Budapest", "9,600,000", "93,028", "Hungarian"),
    ("Iceland", "Reykjavik", "376,000", "103,000", "Icelandic"),
    ("India", "New Delhi", "1,428,000,000", "3,287,263", "Hindi, English"),
    ("Indonesia", "Jakarta", "278,000,000", "1,904,569", "Indonesian"),
    ("Iran", "Tehran", "87,900,000", "1,648,195", "Persian"),
    ("Iraq", "Baghdad", "43,530,000", "438,317", "Arabic, Kurdish"),
    ("Ireland", "Dublin", "5,080,000", "70,273", "Irish, English"),
    ("Israel", "Jerusalem", "9,640,000", "22,072", "Hebrew"),
    ("Italy", "Rome", "58,900,000", "301,339", "Italian"),
    ("Jamaica", "Kingston", "2,830,000", "10,991", "English"),
    ("Japan", "Tokyo", "124,500,000", "377,975", "Japanese"),
    ("Jordan", "Amman", "11,180,000", "89,342", "Arabic"),
    ("Kazakhstan", "Astana", "19,610,000", "2,724,900", "Kazakh, Russian"),
    ("Kenya", "Nairobi", "55,100,000", "580,367", "Swahili, English"),
    ("Kuwait", "Kuwait City", "4,310,000", "17,818", "Arabic"),
    ("Kyrgyzstan", "Bishkek", "6,800,000", "199,951", "Kyrgyz, Russian"),
    ("Laos", "Vientiane", "7,530,000", "236,800", "Lao"),
    ("Latvia", "Riga", "1,870,000", "64,589", "Latvian"),
    ("Lebanon", "Beirut", "5,490,000", "10,452", "Arabic"),
    ("Libya", "Tripoli", "6,870,000", "1,759,540", "Arabic"),
    ("Lithuania", "Vilnius", "2,800,000", "65,300", "Lithuanian"),
    ("Luxembourg", "Luxembourg City", "654,000", "2,586", "Luxembourgish, French, German"),
    ("Madagascar", "Antananarivo", "30,300,000", "587,041", "Malagasy, French"),
    ("Malaysia", "Kuala Lumpur", "33,400,000", "330,803", "Malay"),
    ("Maldives", "Malé", "521,000", "298", "Dhivehi"),
    ("Malta", "Valletta", "535,000", "316", "Maltese, English"),
    ("Mauritius", "Port Louis", "1,266,000", "2,040", "English, French"),
    ("Mexico", "Mexico City", "129,000,000", "1,964,375", "Spanish"),
    ("Moldova", "Chișinău", "2,515,000", "33,851", "Romanian"),
    ("Monaco", "Monaco", "39,000", "2.02", "French"),
    ("Mongolia", "Ulaanbaatar", "3,400,000", "1,564,116", "Mongolian"),
    ("Montenegro", "Podgorica", "620,000", "13,812", "Montenegrin"),
    ("Morocco", "Rabat", "37,840,000", "446,550", "Arabic, Berber"),
    ("Myanmar", "Naypyidaw", "54,580,000", "676,578", "Burmese"),
    ("Namibia", "Windhoek", "2,570,000", "825,615", "English"),
    ("Nepal", "Kathmandu", "30,550,000", "147,181", "Nepali"),
    ("Netherlands", "Amsterdam", "17,700,000", "41,865", "Dutch"),
    ("New Zealand", "Wellington", "5,130,000", "268,021", "English, Māori"),
    ("Nicaragua", "Managua", "6,950,000", "130,373", "Spanish"),
    ("Nigeria", "Abuja", "224,000,000", "923,768", "English"),
    ("North Korea", "Pyongyang", "26,070,000", "120,538", "Korean"),
    ("North Macedonia", "Skopje", "2,070,000", "25,713", "Macedonian"),
    ("Norway", "Oslo", "5,457,000", "385,207", "Norwegian"),
    ("Oman", "Muscat", "4,580,000", "309,500", "Arabic"),
    ("Pakistan", "Islamabad", "241,000,000", "881,913", "Urdu, English"),
    ("Panama", "Panama City", "4,410,000", "75,417", "Spanish"),
    ("Paraguay", "Asunción", "6,780,000", "406,752", "Spanish, Guaraní"),
    ("Peru", "Lima", "33,720,000", "1,285,216", "Spanish, Quechua, Aymara"),
    ("Philippines", "Manila", "117,000,000", "300,000", "Filipino, English"),
    ("Poland", "Warsaw", "36,820,000", "312,696", "Polish"),
    ("Portugal", "Lisbon", "10,350,000", "92,090", "Portuguese"),
    ("Qatar", "Doha", "2,800,000", "11,627", "Arabic"),
    ("Romania", "Bucharest", "19,050,000", "238,397", "Romanian"),
    ("Russia", "Moscow", "144,000,000", "17,098,242", "Russian"),
    ("Rwanda", "Kigali", "13,780,000", "26,338", "Kinyarwanda, English, French"),
    ("Saudi Arabia", "Riyadh", "36,410,000", "2,149,690", "Arabic"),
    ("Senegal", "Dakar", "17,760,000", "196,722", "French"),
    ("Serbia", "Belgrade", "6,690,000", "88,361", "Serbian"),
    ("Singapore", "Singapore", "5,637,000", "733", "English, Malay, Mandarin, Tamil"),
    ("Slovakia", "Bratislava", "5,430,000", "49,035", "Slovak"),
    ("Slovenia", "Ljubljana", "2,110,000", "20,273", "Slovene"),
    ("Somalia", "Mogadishu", "17,070,000", "637,657", "Somali, Arabic"),
    ("South Africa", "Pretoria", "60,140,000", "1,221,037", "11 official languages"),
    ("South Korea", "Seoul", "51,630,000", "100,210", "Korean"),
    ("Spain", "Madrid", "47,480,000", "505,990", "Spanish"),
    ("Sri Lanka", "Sri Jayawardenepura Kotte", "22,040,000", "65,610", "Sinhala, Tamil"),
    ("Sudan", "Khartoum", "48,110,000", "1,886,068", "Arabic, English"),
    ("Sweden", "Stockholm", "10,480,000", "450,295", "Swedish"),
    ("Switzerland", "Bern", "8,800,000", "41,285", "German, French, Italian, Romansh"),
    ("Syria", "Damascus", "22,130,000", "185,180", "Arabic"),
    ("Taiwan", "Taipei", "23,420,000", "36,193", "Mandarin"),
    ("Tajikistan", "Dushanbe", "10,140,000", "143,100", "Tajik"),
    ("Tanzania", "Dodoma", "65,500,000", "945,087", "Swahili, English"),
    ("Thailand", "Bangkok", "71,800,000", "513,120", "Thai"),
    ("Tunisia", "Tunis", "12,360,000", "163,610", "Arabic"),
    ("Turkey", "Ankara", "85,340,000", "783,562", "Turkish"),
    ("Turkmenistan", "Ashgabat", "6,430,000", "488,100", "Turkmen"),
    ("Ukraine", "Kyiv", "37,000,000", "603,628", "Ukrainian"),
    ("United Arab Emirates", "Abu Dhabi", "9,440,000", "83,600", "Arabic"),
    ("United Kingdom", "London", "67,700,000", "242,495", "English"),
    ("United States", "Washington, D.C.", "333,000,000", "9,833,520", "English"),
    ("Uruguay", "Montevideo", "3,420,000", "176,215", "Spanish"),
    ("Uzbekistan", "Tashkent", "35,300,000", "448,978", "Uzbek"),
    ("Vatican City", "Vatican City", "800", "0.49", "Latin, Italian"),
    ("Venezuela", "Caracas", "28,840,000", "916,445", "Spanish"),
    ("Vietnam", "Hanoi", "100,000,000", "331,212", "Vietnamese"),
    ("Yemen", "Sanaa", "34,450,000", "527,968", "Arabic"),
    ("Zimbabwe", "Harare", "16,670,000", "390,757", "English, Shona, Ndebele"),
]


def fetch_articles(titles, max_retries=5):
    """Fetch full text of Wikipedia articles with rate limit handling."""
    articles = {}
    batch_size = 10
    total = len(titles)
    seen_titles = set()
    consecutive_429 = 0

    for start in range(0, total, batch_size):
        batch = titles[start:start + batch_size]
        batch = [t for t in batch if t not in seen_titles]
        if not batch:
            continue
        for t in batch:
            seen_titles.add(t)

        params = {
            "action": "query",
            "titles": "|".join(batch),
            "prop": "extracts",
            "explaintext": True,
            "format": "json",
            "redirects": 1,
        }

        success = False
        for attempt in range(max_retries):
            try:
                resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=30)
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 10 * (attempt + 1)))
                    wait = max(retry_after, 10 * (attempt + 1))
                    logger.warning(f"429 rate limited — waiting {wait}s (attempt {attempt+1})")
                    consecutive_429 += 1
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                consecutive_429 = 0
                data = resp.json()
                pages = data.get("query", {}).get("pages", {})
                for pid, page in pages.items():
                    if pid == "-1":
                        continue
                    title = page.get("title", "")
                    extract = page.get("extract", "")
                    if title and extract and len(extract) > 100:
                        articles[title] = extract
                success = True
                break
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout (attempt {attempt+1})")
                time.sleep(5)
            except Exception as e:
                logger.warning(f"Batch failed (attempt {attempt+1}): {e}")
                time.sleep(5)

        if not success:
            logger.error(f"Giving up on batch: {batch[:2]}...")

        # Exponential backoff if we got rate-limited recently
        if consecutive_429 > 0:
            time.sleep(DELAY * (consecutive_429 + 1))
        else:
            time.sleep(DELAY)

        if (start // batch_size) % 10 == 0:
            logger.info(f"Fetched {len(articles)} articles ({start}/{total})")

    return articles


def make_entries(articles):
    """Convert fetched articles into chunked knowledge entries."""
    entries = []
    for title, text in sorted(articles.items()):
        chunks = chunk_text(text, max_chars=1500, overlap=100)
        source = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        if len(chunks) == 1:
            entries.append({
                "title": title,
                "content": chunks[0],
                "source": source,
                "type": "wikipedia"
            })
        else:
            for i, chunk in enumerate(chunks):
                entries.append({
                    "title": f"{title} (part {i+1})",
                    "content": chunk,
                    "source": f"{source}#p{i+1}",
                    "type": "wikipedia"
                })
    return entries


def make_country_entries():
    """Create structured entries for all UN countries."""
    entries = []
    for name, capital, population, area, languages in COUNTRIES:
        text = (
            f"{name} is a country. Capital: {capital}. "
            f"Population: {population}. Area: {area} sq km. "
            f"Official languages: {languages}."
        )
        entries.append({
            "title": name,
            "content": text,
            "source": f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}",
            "type": "geography"
        })
    return entries


def main():
    logger.info("=" * 60)
    logger.info("Viora AI Knowledge Base Seeder")
    logger.info("=" * 60)

    # Step 1: Fetch Wikipedia articles
    logger.info(f"\nFetching {len(ALL_TITLES)} curated Wikipedia articles...")
    articles = fetch_articles(ALL_TITLES)
    logger.info(f"Successfully fetched {len(articles)} articles with content.")

    # Step 2: Create entries
    logger.info("\nCreating knowledge entries...")
    wiki_entries = make_entries(articles)
    country_entries = make_country_entries()
    all_entries = wiki_entries + country_entries

    logger.info(f"Wikipedia article chunks: {len(wiki_entries)}")
    logger.info(f"Country entries: {len(country_entries)}")
    logger.info(f"Total entries: {len(all_entries)}")

    total_chars = sum(len(e["content"]) for e in all_entries)
    logger.info(f"Total content size: {total_chars:,} chars (~{total_chars / (1024*1024):.1f} MB)")

    # Step 3: Clear old knowledge and save new
    logger.info("\nSaving to knowledge base (replacing old entries)...")
    from knowledge import save
    from pathlib import Path
    save(all_entries)

    # Step 4: Rebuild index
    logger.info("\nRebuilding TF-IDF search index...")
    count = rebuild_index()
    logger.info(f"Index rebuilt: {count} documents")

    # Step 5: Show stats
    from knowledge import stats
    s = stats()
    logger.info(f"\n{'='*60}")
    logger.info(f"Knowledge base ready!")
    logger.info(f"  Entries: {s['total_entries']}")
    logger.info(f"  Total chars: {s['total_chars']:,}")
    logger.info(f"  File size: {s['file_size_mb']} MB")
    logger.info(f"  Embedder: {'available' if s['embedder_available'] else 'not available'}")
    logger.info(f"  Types: {json.dumps(s['type_breakdown'], indent=2)}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
