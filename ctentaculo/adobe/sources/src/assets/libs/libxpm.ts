const comment_regex = /\s*\/\*.*\*\/\s*/g
let render_options = {
  scale: 10,
  bg_checkered: false,
}

const colorPixel = (c, x, y, color) => {
  var xx, yy
  xx = x * render_options.scale
  yy = y * render_options.scale
  if (color) {
    if (color.match(/none/i)) {
      if (render_options.bg_checkered) {
        var step = render_options.scale / 2
        c.fillStyle = '#333'
        c.fillRect(xx, yy, step, step)
        c.fillRect(xx + step, yy + step, step, step)
      }
    } else {
      c.fillStyle = color
      c.fillRect(xx, yy, render_options.scale, render_options.scale)
    }
  }
}

export default class XPMParser {
  static xpmToData(what, options?) {
    if (!what) return null
    if (options) render_options = options
    var xpm_info = this.parseXpm(what)
    var canvas = document.createElement('canvas')
    XPMParser.renderToCanvas(xpm_info, canvas)
    var data = canvas.toDataURL()
    return data
  }

  static parseXpm(what) {
    var xpm_info: any = {}
    var body = what
      .substring(what.indexOf('{') + 1, what.lastIndexOf('}'))
      .trim()
    var lines: string[] = [],
      line
    var sp = body.split(',\n')
    for (var k = 0; k < sp.length; k++) {
      line = sp[k]
      line = line
        .replace(comment_regex, '')
        .trim()
        .replace(/"/g, '')
      if (line != '') {
        lines.push(line)
      }
    }
    var info_line: string = lines[0]
    var info_parts = info_line.trim().split(/\s+/)
    xpm_info.width = parseInt(info_parts[0])
    xpm_info.height = parseInt(info_parts[1])
    xpm_info.num_colors = parseInt(info_parts[2])
    xpm_info.cpp = parseInt(info_parts[3])
    var i
    var color_map = {},
      parts,
      char,
      color,
      color_split,
      colorInfo
    for (i = 1; i <= xpm_info.num_colors; i++) {
      colorInfo = lines[i].split(' ')
      char = colorInfo[0]
      color_map[char] = colorInfo[2]
    }
    xpm_info.color_map = color_map
    xpm_info.pixels = lines.slice(i)
    return xpm_info
  }

  static renderToCanvas(xpm_info, c, options?: any) {
    if (options) render_options = options
    c.height = xpm_info.height * render_options.scale
    c.width = xpm_info.width * render_options.scale
    var ctx = c.getContext('2d')
    var pixels = xpm_info.pixels
    for (var i = 0; i < pixels.length; i++) {
      let line = pixels[i]
      for (var j = 0; j < line.length / xpm_info.cpp; j++) {
        let char = line.substr(j * xpm_info.cpp, xpm_info.cpp)
        colorPixel(ctx, j, i, xpm_info.color_map[char])
      }
    }
  }
}
