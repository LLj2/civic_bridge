# Themes Configuration

This directory contains the configurable themes and email templates for the Civic Bridge composer.

## Configuration Files

### themes.json
Contains all themes, topics, and email templates. Structure:

```json
{
  "version": "1.0",
  "updated": "2025-01-28",
  "templates": {
    "subject": "Template with {placeholders}",
    "body": {
      "greeting": "Greeting template",
      "introduction": "Introduction template",
      "topics_header": "Topics header",
      "closing": "Closing template"
    }
  },
  "themes": {
    "theme_key": {
      "title": "Display Name",
      "description": "Description for tooltip",
      "topics": [
        {
          "id": "topic_id",
          "label": "Topic display label",
          "description": "Topic description"
        }
      ]
    }
  }
}
```

## Available Placeholders

### Subject Template
- `{comune}` - User's city name
- `{tema}` - Selected theme title

### Body Templates
- `{titolo}` - Representative's formal title (Onorevole, Senatore, etc.)
- `{cognome}` - Representative's last name  
- `{comune}` - User's city name
- `{tema}` - Selected theme title

## Editing Themes

1. **Edit themes.json** directly in this directory
2. **Restart the Flask server** for changes to take effect
3. **Test changes** by selecting themes in the composer

## Current Themes

1. **Guerra in Palestina** - Issues related to Israel-Palestine conflict
2. **Politiche di migrazione** - European migration policies
3. **Ambiente e clima** - Environmental and climate policies  
4. **Lavoro e politiche sociali** - Labor and social policies
5. **Sanità pubblica** - Public health policies
6. **Economia e sviluppo** - Economic and development policies
7. **Diritti civili e libertà** - Civil rights and freedoms
8. **Altro argomento** - For other topics (no predefined topics)

## Adding New Themes

1. Add a new key to the `themes` object
2. Provide `title` and optional `description`
3. Add `topics` array with `id`, `label`, and optional `description`
4. Restart server to load changes

Example:
```json
"nuovo_tema": {
  "title": "Nuovo Tema",
  "description": "Descrizione del nuovo tema",
  "topics": [
    {
      "id": "topic1",
      "label": "Primo argomento", 
      "description": "Descrizione del primo argomento"
    }
  ]
}
```

## API Endpoint

The configuration is served via `/api/themes` and automatically loaded by the frontend. If the config file is missing, the system uses fallback themes.

## Troubleshooting

- **Themes not loading**: Check server logs for JSON syntax errors
- **Missing themes**: Verify `themes.json` exists in `config/` directory
- **Template errors**: Check placeholder syntax matches available variables