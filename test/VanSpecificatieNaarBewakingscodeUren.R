
# Benodigde packages
library(tibble)
library(readr)
library(dplyr)

# pad naar folder met csv-bestanden
input_folder <-  file.path(getwd(),"GevelConcept_ProcessAnalyticsRapport", "specificatieuren")

# Vertaaltabel die specificatiecode koppelt aan een bewakingscode
vertaaltabel <- tibble(
  specificatiecode = c("020CAL", "035FRE", "040CON", "050BIE", "055ORD", 
                       "060SEL", "070LAT", "080OPK", "090SPU", "100AFM", 
                       "110GLZ", "AFM","085VMO"),
  Omschrijving = c("Afkorten en calibreren", "Frezen", "Conturex", "Biesse", 
                   "Opsluite ramen/deuren", "Select", "Afkort/ProfielContr Lat", 
                   "opsluiten kozijnen", "Spuiten", "Afmontage", 
                   "Glaszetten (extern)", "afmonteren", "Voormontage/glaslatten"),
  bewakingscode = c("K601", "K601", "K602", "K601", "K603", "K601", "K603", 
                    "K603", "K604", "K605", NA, "K605","K603")
)

# Pad naar input folder
csv_bestanden <- list.files(input_folder, 
                            pattern = "\\.csv$",
                            full.names = TRUE,
                            ignore.case = TRUE)

# Initialiseer lege lijst voor geldige data
alle_data_lijst <- list()
niet_behandeld <- vector("character")

# Loop door alle bestanden
# Loop door alle bestanden
for (bestand in csv_bestanden) {
  cat("Verwerk:", basename(bestand), "\n")
  
  tryCatch({
    # Lees EERST cel 1A (rij 1, kolom 1)
    cel_1A <- read_delim(bestand, 
                         delim = ";",
                         n_max = 1,        # alleen eerste rij lezen
                         col_names = FALSE, # geen kolomnamen
                         locale = locale(decimal_mark = ","),
                         show_col_types = FALSE)
    
    # Haal de waarde uit cel 1A (eerste cel van eerste rij)
    project_code_vlak <- as.character(cel_1A[1, 1])
    
    # Lees NU de data vanaf rij 4
    data <- read_delim(bestand, 
                       delim = ";",
                       skip = 3,
                       col_names = TRUE,
                       locale = locale(decimal_mark = ","),
                       show_col_types = FALSE)
    
    # Check of tweede kolom 'Omschrijving' is
    if (length(names(data)) >= 2 && names(data)[2] == "Omschrijving") {
      cat("  ✓ Geldig bestand | Cel 1A:", project_code_vlak, "\n")
      
      # Voeg project_code toe als kolom (niet bestandsnaam!)
      data <- data %>%
        mutate(project = project_code_vlak)
      
      # Voeg toe aan lijst
      alle_data_lijst[[length(alle_data_lijst) + 1]] <- data
    } else {
      cat("  ✗ Ongeldig: tweede kolom is niet 'Omschrijving'\n")
      niet_behandeld <- c(niet_behandeld, basename(bestand))
    }
  }, error = function(e) {
    cat("  ✗ Fout bij inlezen:", e$message, "\n")
    niet_behandeld <- c(niet_behandeld, basename(bestand))
  })
  
  cat("---\n")
}

# Combineer alle geldige dataframes
if (length(alle_data_lijst) > 0) {
  alle_data <- bind_rows(alle_data_lijst)
  
  # Verplaats 'bestand' kolom naar eerste positie 
  alle_data <- alle_data %>%
    select(project, everything())
  
} else {
  cat("Geen geldige bestanden gevonden.\n")
  alle_data <- data.frame()  # lege dataframe
}
# Toon niet-behandelde bestanden
if (length(niet_behandeld) > 0) {
  cat("\n════════════════════════════════════════\n")
  cat("NIET BEHANDELDE BESTANDEN:\n")
  cat("════════════════════════════════════════\n")
  cat("Aantal:", length(niet_behandeld), "\n")
  cat("Bestanden:\n")
  for (bestand in niet_behandeld) {
    cat("-", bestand, "\n")
  }
} else {
  cat("\n════════════════════════════════════════\n")
  cat("ALLES SUCCESVOL BEHANDELD\n")
  cat("════════════════════════════════════════\n")
  cat("Alle CSV-bestanden zijn correct ingelezen.\n")
}


data_opgeschoond <- alle_data %>%
  mutate(
    projectcode = gsub("SPECIFICATIE UREN van project: ", "", project)) %>%
  select(-project) %>%
  rename(specificatiecode = 1)


## Linken bewakingscode aan specificatiecode
data_opgeschoond <- data_opgeschoond %>%
  left_join(vertaaltabel, by = "specificatiecode")

uren_per_bewakingscode <- data_opgeschoond %>%
  group_by(bewakingscode,projectcode) %>%
  summarize(
    uren = sum(Uren...4)
  ) %>%
  filter(!is.na(bewakingscode)) %>%
  pivot_wider(
    names_from = bewakingscode,      # Column whose values will become new column names
    values_from = uren,               # Column whose values will fill the new columns
    names_prefix = "",               # Optional: Remove if you don't want a prefix
    names_sep = "_",                 # Separator between bewakingscode and "uren"
    values_fill = 0                  # Optional: Fill missing values with 0 (or NA if omitted)
  ) 

# Kolomnamen aanpassen
nieuwe_kolomnamen <- c(
  colnames(uren_per_bewakingscode)[1],               # Projectcode kolomnaam niet aanpassen
  paste0(colnames(uren_per_bewakingscode)[2:ncol(uren_per_bewakingscode)], "_uren")  # Uren toevoegen aan bewakingscode kolomnaam
)

# Nieuwe kolomnamen toewijzen aan de tabel
colnames(uren_per_bewakingscode) <- nieuwe_kolomnamen
  

write.csv2(uren_per_bewakingscode, "uren_per_bewakingscode.csv", row.names = FALSE)
write.csv(uren_per_bewakingscode, "eng_uren_per_bewakingscode.csv", row.names= FALSE)
  