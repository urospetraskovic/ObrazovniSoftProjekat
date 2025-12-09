from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# Create PDF
pdf_path = "raw_materials/climate_change_lesson.pdf"
doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)

# Container for PDF elements
elements = []

# Define styles
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor='#1a1a1a',
    spaceAfter=30,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=14,
    textColor='#333333',
    spaceAfter=12,
    spaceBefore=12,
    fontName='Helvetica-Bold'
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['BodyText'],
    fontSize=11,
    alignment=TA_JUSTIFY,
    spaceAfter=12,
    leading=16
)

# Content
title = Paragraph("CLIMATE CHANGE: UNDERSTANDING GLOBAL WARMING", title_style)
elements.append(title)
elements.append(Spacer(1, 0.2*inch))

# Introduction
intro = Paragraph(
    "Climate change represents one of the most pressing challenges facing humanity in the twenty-first century. The Earth's climate has undergone significant shifts in recent decades, with global temperatures rising at an unprecedented rate. Scientists estimate that the planet has warmed by approximately 1.1 degrees Celsius since pre-industrial times, with most of this warming occurring in the last fifty years. This phenomenon, commonly known as global warming or climate change, is driven primarily by human activities that increase the concentration of greenhouse gases in the atmosphere. The consequences of climate change are far-reaching, affecting weather patterns, sea levels, ecosystems, and human societies worldwide. Understanding the causes, effects, and potential solutions to climate change is essential for developing effective strategies to mitigate its impacts and adapt to the changes already underway.",
    body_style
)
elements.append(intro)
elements.append(Spacer(1, 0.15*inch))

# Greenhouse Gases
elements.append(Paragraph("Greenhouse Gases and the Greenhouse Effect", heading_style))
greenhouse_text = Paragraph(
    "The greenhouse effect is a natural process that has allowed life to exist on Earth by maintaining the planet's temperature at habitable levels. Certain gases in the atmosphere, including carbon dioxide, methane, nitrous oxide, and water vapor, trap heat from the sun and prevent it from escaping back into space. This natural blanket of gases keeps Earth approximately 60 degrees Fahrenheit warmer than it would otherwise be. However, since the industrial revolution, human activities have dramatically increased the concentration of these greenhouse gases. Burning fossil fuels such as coal, oil, and natural gas for energy releases carbon dioxide into the atmosphere. Agriculture, particularly livestock farming, produces significant amounts of methane. Industrial processes and waste decomposition release nitrous oxide. As the concentration of these gases increases, more heat becomes trapped, causing the planet to warm. Carbon dioxide, the primary greenhouse gas responsible for climate change, has increased by over 40 percent since pre-industrial times, rising from approximately 280 parts per million to over 420 parts per million today.",
    body_style
)
elements.append(greenhouse_text)
elements.append(Spacer(1, 0.15*inch))

# Human Activities
elements.append(Paragraph("Human Activities Driving Climate Change", heading_style))
activities_text = Paragraph(
    "The primary driver of modern climate change is the burning of fossil fuels for electricity, heat, and transportation. Coal power plants, oil refineries, and natural gas facilities emit enormous quantities of carbon dioxide daily. The transportation sector, including cars, airplanes, and ships, contributes significantly to global emissions. Agriculture is another major contributor, both through the production of methane by livestock and through the use of chemical fertilizers that release nitrous oxide. Deforestation exacerbates the problem by removing trees that would otherwise absorb carbon dioxide through photosynthesis. Industrial manufacturing processes release various greenhouse gases and other pollutants. While developing nations are often associated with emissions growth due to industrialization, developed nations historically have produced the majority of atmospheric carbon dioxide through a century of industrial activity. Today, China leads in total emissions, followed by the United States and India. However, per capita emissions reveal that developed nations typically emit far more greenhouse gases per person than developing nations.",
    body_style
)
elements.append(activities_text)
elements.append(Spacer(1, 0.15*inch))

# Effects on Climate
elements.append(Paragraph("Effects of Climate Change", heading_style))
effects_text = Paragraph(
    "Rising global temperatures produce cascading effects throughout Earth's climate system. Warming ocean waters expand, causing sea levels to rise, which threatens coastal communities and island nations. Melting glaciers and ice sheets, particularly in Greenland and Antarctica, contribute additional water to oceans, accelerating sea level rise. Higher temperatures intensify the water cycle, leading to more frequent and severe droughts in some regions and excessive rainfall and flooding in others. Hurricane and typhoon intensification occurs as warmer ocean water provides additional energy for these storm systems. Permafrost in polar and high-mountain regions is thawing, releasing methane and carbon dioxide that had been trapped for millennia, creating a positive feedback loop that accelerates warming. Weather patterns are becoming more unpredictable, with unprecedented heat waves, cold snaps, and precipitation extremes occurring with increasing frequency. Spring arrives earlier, disrupting the timing of plant flowering and animal migration that had evolved over thousands of years.",
    body_style
)
elements.append(effects_text)
elements.append(Spacer(1, 0.15*inch))

# Environmental and Biological Impacts
elements.append(Paragraph("Environmental and Biological Impacts", heading_style))
bio_text = Paragraph(
    "Climate change poses severe threats to ecosystems and biodiversity worldwide. Many species are unable to adapt quickly enough to rapidly changing conditions and face extinction. Coral reefs, which support approximately one-quarter of all marine species despite covering less than one percent of the ocean floor, are bleaching in response to warmer water temperatures. Fish populations are shifting toward cooler waters, affecting both marine ecosystems and human food security. Forest ecosystems are experiencing increased stress from drought, heat, and insect outbreaks. Polar bears and other Arctic species face habitat loss as sea ice diminishes. Amphibians are particularly vulnerable to climate change due to their dependence on specific moisture and temperature conditions. Agricultural productivity is threatened by changing rainfall patterns, extended growing seasons in some regions, and shortened seasons in others. Some plant and animal species are experiencing range shifts, moving toward the poles or to higher elevations in pursuit of suitable climatic conditions. However, many species cannot migrate fast enough to follow their preferred climate, leading to local extinctions and reduced biodiversity.",
    body_style
)
elements.append(bio_text)
elements.append(Spacer(1, 0.15*inch))

# Human Society Impacts
elements.append(Paragraph("Impacts on Human Society", heading_style))
human_text = Paragraph(
    "The effects of climate change on human societies are profound and multifaceted. Rising sea levels threaten major cities and agricultural regions in low-lying coastal areas, potentially displacing hundreds of millions of people. Water scarcity is expected to affect billions of people, particularly in regions dependent on glacial meltwater for irrigation and drinking water. Agricultural yields may decline in many regions due to drought, flooding, and changing pest distributions. Heat waves pose direct health risks, particularly for vulnerable populations including the elderly and those with chronic illnesses. Air quality deteriorates due to increased ground-level ozone and particulate matter formation under warmer conditions. Disease transmission patterns are changing, with tropical diseases expanding their geographic range toward the poles. Economic impacts are substantial, including costs associated with property damage from extreme weather, agricultural losses, health care expenses, and infrastructure damage. Developing nations and low-income populations, despite having contributed least to the problem, face the greatest risks and have the fewest resources to adapt. Climate change also threatens geopolitical stability through resource competition, particularly over water and arable land, potentially leading to climate migration and conflict.",
    body_style
)
elements.append(human_text)
elements.append(Spacer(1, 0.15*inch))

# Solutions and Mitigation
elements.append(Paragraph("Solutions and Mitigation Strategies", heading_style))
solutions_text = Paragraph(
    "Addressing climate change requires both mitigation strategies that reduce greenhouse gas emissions and adaptation strategies that help societies cope with unavoidable changes. Transitioning to renewable energy sources, including solar, wind, hydroelectric, and geothermal power, can substantially reduce emissions from electricity generation. Energy efficiency improvements in buildings, transportation, and industry can lower energy consumption. Electrification of vehicles and development of sustainable transportation alternatives reduce fossil fuel dependence. Protecting and expanding forests through reforestation and preventing deforestation preserves natural carbon sinks. Developing carbon capture and storage technologies can remove carbon dioxide from the atmosphere. Agriculture can become more sustainable through conservation practices and reducing livestock emissions. International agreements like the Paris Climate Accord establish frameworks for coordinated global action. Many countries are implementing carbon pricing systems and renewable energy mandates to accelerate the transition away from fossil fuels. Individual actions also matter, including adopting plant-based diets, reducing energy consumption, supporting sustainable companies, and advocating for climate policies. However, scientists emphasize that limiting warming to 1.5 or 2 degrees Celsius above pre-industrial levels requires immediate and dramatic reductions in global emissions.",
    body_style
)
elements.append(solutions_text)
elements.append(Spacer(1, 0.15*inch))

# Future Outlook
elements.append(Paragraph("Future Outlook and International Response", heading_style))
future_text = Paragraph(
    "The future trajectory of climate change depends largely on actions taken in the present decade. Scientific projections indicate that without significant emissions reductions, global temperatures could rise by 3 degrees Celsius or more by the end of the century, causing catastrophic impacts. The Intergovernmental Panel on Climate Change, established by the United Nations, regularly assesses climate science and has concluded with high confidence that human activities are the dominant cause of climate change. International conferences, including the annual Conference of the Parties to the United Nations Framework Convention on Climate Change, bring nations together to negotiate emissions reduction targets and climate adaptation funding. The transition to sustainable energy systems, circular economies, and climate-resilient agriculture represents a massive economic transformation comparable to previous industrial revolutions. Many countries and companies are committing to net-zero emissions targets, pledging to reduce emissions to zero by mid-century. Technological innovation continues to make renewable energy cheaper and more efficient. However, political will, financial investment, and behavioral change remain critical challenges. The decisions made by governments, corporations, and individuals in the coming years will largely determine the severity of climate impacts experienced by future generations.",
    body_style
)
elements.append(future_text)
elements.append(Spacer(1, 0.15*inch))

# Conclusion
elements.append(Paragraph("Conclusion", heading_style))
conclusion_text = Paragraph(
    "Climate change is not a distant future threat but a present reality reshaping our world. The evidence is overwhelming that human activities, particularly the burning of fossil fuels and deforestation, have caused rapid and unprecedented warming of the Earth's climate system. The consequences are already visible through melting ice, rising seas, shifting ecosystems, and changing weather patterns. However, the situation is not hopeless. Human societies have the technological knowledge and economic capacity to transition to sustainable systems that do not destabilize the climate. What is required is the collective will to prioritize climate action, invest in renewable energy and sustainable practices, and make difficult but necessary changes to how we produce energy, grow food, and organize our economies. Every fraction of a degree of warming prevented through emissions reductions reduces the severity of future impacts. By understanding the science of climate change and supporting evidence-based policies, individuals and societies can contribute to safeguarding the climate system and ensuring a sustainable future for all humanity.",
    body_style
)
elements.append(conclusion_text)

# Build PDF
doc.build(elements)
print(f"PDF created successfully: {pdf_path}")
