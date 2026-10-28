/* Auto-generated from desktop/navix/server.py. Do not edit manually. */
export const PUBLIC_TOOLS = Object.freeze([
  {
    "name": "status",
    "title": "Status",
    "description": "Estado real das permissões e tempo restante da sessão local.",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_tabs",
    "title": "Browser tabs",
    "description": "Lista abas do navegador de automação aberto pelo proprietário.",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_open",
    "title": "Browser open",
    "description": "Abre URL HTTP/HTTPS numa nova aba do perfil de automação.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "url": {
          "type": "string"
        }
      },
      "required": [
        "url"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_read",
    "title": "Browser read",
    "description": "Lê até 30 mil caracteres visíveis da aba.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        }
      },
      "required": [
        "page_id"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_click",
    "title": "Browser click",
    "description": "Clica um elemento pelo papel acessível e nome exato, sem ambiguidades.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        },
        "role": {
          "type": "string"
        },
        "name": {
          "type": "string"
        }
      },
      "required": [
        "page_id",
        "role",
        "name"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_fill",
    "title": "Browser fill",
    "description": "Preenche um campo identificado por papel e nome acessível exatos.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        },
        "role": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "text": {
          "type": "string"
        }
      },
      "required": [
        "page_id",
        "role",
        "name",
        "text"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_scroll",
    "title": "Browser scroll",
    "description": "Rola verticalmente uma aba, até 2000 pixels por chamada.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        },
        "pixels": {
          "type": "integer"
        }
      },
      "required": [
        "page_id",
        "pixels"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_screenshot",
    "title": "Browser screenshot",
    "description": "Captura a área visível da aba autorizada.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        }
      },
      "required": [
        "page_id"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "desktop_screenshot",
    "title": "Desktop screenshot",
    "description": "Captura a tela inteira somente com permissão de desktop ativa.",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "desktop_click",
    "title": "Desktop click",
    "description": "Clica numa coordenada válida da tela; exige sessão autorizada.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "x": {
          "type": "integer"
        },
        "y": {
          "type": "integer"
        },
        "button": {
          "type": "string",
          "default": "left"
        },
        "clicks": {
          "type": "integer",
          "default": 1
        }
      },
      "required": [
        "x",
        "y"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "desktop_type",
    "title": "Desktop type",
    "description": "Digita texto na janela em foco, com suporte a acentos no Windows.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "text": {
          "type": "string"
        }
      },
      "required": [
        "text"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "desktop_key",
    "title": "Desktop key",
    "description": "Pressiona uma tecla reconhecida pelo teclado do Windows.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "key": {
          "type": "string"
        }
      },
      "required": [
        "key"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "desktop_scroll",
    "title": "Desktop scroll",
    "description": "Rola o mouse até 20 passos por chamada.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "steps": {
          "type": "integer"
        }
      },
      "required": [
        "steps"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "desktop_position",
    "title": "Desktop position",
    "description": "Retorna a posição atual do cursor do mouse.",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "desktop_screen_info",
    "title": "Desktop screen info",
    "description": "Dimensões da tela principal e posição do cursor.",
    "inputSchema": {
      "type": "object",
      "properties": {},
      "required": [],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "desktop_move",
    "title": "Desktop move",
    "description": "Move o cursor para uma coordenada da tela.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "x": {
          "type": "integer"
        },
        "y": {
          "type": "integer"
        },
        "duration": {
          "type": "number",
          "default": 0.2
        }
      },
      "required": [
        "x",
        "y"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "desktop_drag",
    "title": "Desktop drag",
    "description": "Arrasta do cursor atual até uma coordenada da tela.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "x": {
          "type": "integer"
        },
        "y": {
          "type": "integer"
        },
        "duration": {
          "type": "number",
          "default": 0.5
        },
        "button": {
          "type": "string",
          "default": "left"
        }
      },
      "required": [
        "x",
        "y"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "desktop_hotkey",
    "title": "Desktop hotkey",
    "description": "Executa combinação de teclas, por exemplo ['ctrl', 's'] ou ['alt', 'tab'].",
    "inputSchema": {
      "type": "object",
      "properties": {
        "keys": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "keys"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_start",
    "title": "Browser start",
    "description": "Abre o navegador integrado ou Opera com perfil separado autorizado.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "kind": {
          "type": "string",
          "default": "integrado"
        }
      },
      "required": [],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_navigate",
    "title": "Browser navigate",
    "description": "Navega uma aba existente para uma URL HTTP/HTTPS.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        },
        "url": {
          "type": "string"
        }
      },
      "required": [
        "page_id",
        "url"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_close_tab",
    "title": "Browser close tab",
    "description": "Fecha uma aba do perfil de automação.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        }
      },
      "required": [
        "page_id"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_back",
    "title": "Browser back",
    "description": "Volta à página anterior na aba.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        }
      },
      "required": [
        "page_id"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_forward",
    "title": "Browser forward",
    "description": "Avança no histórico da aba.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        }
      },
      "required": [
        "page_id"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_reload",
    "title": "Browser reload",
    "description": "Recarrega a página e aguarda o DOM.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        }
      },
      "required": [
        "page_id"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_snapshot",
    "title": "Browser snapshot",
    "description": "Árvore acessível com nomes e funções dos elementos para localizar campos e botões.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        }
      },
      "required": [
        "page_id"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_select",
    "title": "Browser select",
    "description": "Seleciona valores em uma lista HTML identificada por nome e função exatos.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        },
        "role": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "values": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "page_id",
        "role",
        "name",
        "values"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_press",
    "title": "Browser press",
    "description": "Pressiona tecla ou atalho em um elemento identificado, por exemplo Enter.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        },
        "role": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "key": {
          "type": "string"
        }
      },
      "required": [
        "page_id",
        "role",
        "name",
        "key"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_hover",
    "title": "Browser hover",
    "description": "Posiciona o mouse sobre um elemento da página.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        },
        "role": {
          "type": "string"
        },
        "name": {
          "type": "string"
        }
      },
      "required": [
        "page_id",
        "role",
        "name"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_wait",
    "title": "Browser wait",
    "description": "Aguarda estado de um elemento, até 30 segundos.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        },
        "role": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "state": {
          "type": "string",
          "default": "visible"
        },
        "timeout_ms": {
          "type": "integer",
          "default": 10000
        }
      },
      "required": [
        "page_id",
        "role",
        "name"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_upload",
    "title": "Browser upload",
    "description": "Seleciona arquivos locais em input[type=file]; exige navegador e arquivos.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        },
        "selector": {
          "type": "string"
        },
        "paths": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "page_id",
        "selector",
        "paths"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "browser_download",
    "title": "Browser download",
    "description": "Clica um link/botão de download e salva no caminho local explícito, sem sobrescrever.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "page_id": {
          "type": "string"
        },
        "role": {
          "type": "string"
        },
        "name": {
          "type": "string"
        },
        "destination": {
          "type": "string"
        },
        "timeout_ms": {
          "type": "integer",
          "default": 30000
        }
      },
      "required": [
        "page_id",
        "role",
        "name",
        "destination"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_list",
    "title": "Files list",
    "description": "Lista arquivos e subpastas de um diretório local.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        },
        "limit": {
          "type": "integer",
          "default": 500
        }
      },
      "required": [
        "path"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_read",
    "title": "Files read",
    "description": "Lê um arquivo UTF-8, indicando truncamento quando exceder o limite.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        },
        "max_bytes": {
          "type": "integer",
          "default": 1000000
        }
      },
      "required": [
        "path"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_write",
    "title": "Files write",
    "description": "Cria arquivo UTF-8; substituir um existente exige overwrite=true.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        },
        "text": {
          "type": "string"
        },
        "overwrite": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [
        "path",
        "text"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": true,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_edit",
    "title": "Files edit",
    "description": "Substitui texto exato num arquivo. Recusa correspondência ambígua sem replace_all.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        },
        "old_text": {
          "type": "string"
        },
        "new_text": {
          "type": "string"
        },
        "replace_all": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [
        "path",
        "old_text",
        "new_text"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": true,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_mkdir",
    "title": "Files mkdir",
    "description": "Cria uma pasta no caminho indicado.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        },
        "parents": {
          "type": "boolean",
          "default": true
        }
      },
      "required": [
        "path"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_copy",
    "title": "Files copy",
    "description": "Copia arquivo ou pasta para um destino explícito.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "source": {
          "type": "string"
        },
        "destination": {
          "type": "string"
        },
        "overwrite": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [
        "source",
        "destination"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_move",
    "title": "Files move",
    "description": "Move ou renomeia arquivo/pasta; não sobrescreve por padrão.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "source": {
          "type": "string"
        },
        "destination": {
          "type": "string"
        },
        "overwrite": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [
        "source",
        "destination"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": true,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_delete",
    "title": "Files delete",
    "description": "Apaga permanentemente um arquivo ou pasta vazia. Árvore de pastas exige recursive=true.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        },
        "recursive": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [
        "path"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": true,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_read_binary",
    "title": "Files read binary",
    "description": "Retorna arquivo em base64 para transferir ao cliente MCP.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        },
        "max_bytes": {
          "type": "integer",
          "default": 5000000
        }
      },
      "required": [
        "path"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": true,
      "destructiveHint": false,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_write_binary",
    "title": "Files write binary",
    "description": "Recebe conteúdo base64 do cliente MCP e grava arquivo binário local.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        },
        "content_base64": {
          "type": "string"
        },
        "overwrite": {
          "type": "boolean",
          "default": false
        }
      },
      "required": [
        "path",
        "content_base64"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": true,
      "openWorldHint": false
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "files_download",
    "title": "Files download",
    "description": "Baixa HTTP/HTTPS para caminho local, com limite de tempo e tamanho.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "url": {
          "type": "string"
        },
        "destination": {
          "type": "string"
        },
        "overwrite": {
          "type": "boolean",
          "default": false
        },
        "max_bytes": {
          "type": "integer",
          "default": 100000000
        },
        "timeout_seconds": {
          "type": "integer",
          "default": 30
        }
      },
      "required": [
        "url",
        "destination"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": false,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "command_run",
    "title": "Command run",
    "description": "Executa PowerShell, cmd ou Python, retornando saída e código de término. Exige comandos.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "command": {
          "type": "string"
        },
        "shell": {
          "type": "string",
          "default": "powershell"
        },
        "cwd": {
          "type": "string",
          "default": ""
        },
        "timeout_seconds": {
          "type": "integer",
          "default": 60
        }
      },
      "required": [
        "command"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": true,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  },
  {
    "name": "command_exec",
    "title": "Command exec",
    "description": "Executa programa por lista de argumentos, sem interpretação implícita por shell.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "argv": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "cwd": {
          "type": "string",
          "default": ""
        },
        "timeout_seconds": {
          "type": "integer",
          "default": 60
        }
      },
      "required": [
        "argv"
      ],
      "additionalProperties": false
    },
    "annotations": {
      "readOnlyHint": false,
      "destructiveHint": true,
      "openWorldHint": true
    },
    "_meta": {
      "securitySchemes": [
        {
          "type": "oauth2",
          "scopes": [
            "navix:control"
          ]
        }
      ]
    }
  }
]);
